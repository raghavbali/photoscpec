"""Metadata-free photo and print-sheet export."""
from io import BytesIO
import math

from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import ExportResult, PhotoExportRequest, SheetExportRequest
from ._image import open_image, rgb_on_white
from .layout import calculate_layout

MM_TO_PT = 72 / 25.4
MAX_SHEET_PIXELS = 100_000_000


def _dpi(dpi: int) -> None:
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0 or dpi > 2400:
        raise PhotoScpecError("invalid_dpi", "DPI must be an integer from 1 to 2400")


def _encode(image: Image.Image, fmt: str, dpi: int) -> ExportResult:
    fmt = fmt.upper()
    if fmt == "JPG":
        fmt = "JPEG"
    if fmt not in {"PNG", "JPEG"}:
        raise PhotoScpecError("unsupported_export_format", "Photo format must be PNG or JPG")
    output = BytesIO()
    options = {"dpi": (dpi, dpi)}
    if fmt == "JPEG":
        options.update(quality=95, subsampling=0)
    image.save(output, fmt, **options)
    extension = "jpg" if fmt == "JPEG" else "png"
    return ExportResult(output.getvalue(), f"image/{'jpeg' if fmt == 'JPEG' else 'png'}",
                        f"photo.{extension}")


def export_photo(request: PhotoExportRequest) -> ExportResult:
    _dpi(request.dpi)
    return _encode(rgb_on_white(open_image(request.image)), request.format, request.dpi)


def export_sheet(request: SheetExportRequest) -> ExportResult:
    _dpi(request.dpi)
    layout = calculate_layout(request.layout)
    photo = rgb_on_white(open_image(request.image))
    fmt = request.format.upper()
    if fmt == "PDF":
        output = BytesIO()
        canvas = Canvas(output, pagesize=(layout.paper_width_mm * MM_TO_PT,
                                          layout.paper_height_mm * MM_TO_PT),
                        pageCompression=1)
        image_data = BytesIO()
        photo.save(image_data, "PNG")
        reader = ImageReader(image_data)
        for placement in layout.positions:
            rendered = photo.rotate(-90, expand=True) if placement.rotated else photo
            data = BytesIO()
            rendered.save(data, "PNG")
            canvas.drawImage(ImageReader(data), placement.x_mm * MM_TO_PT,
                             (layout.paper_height_mm - placement.y_mm -
                              placement.height_mm) * MM_TO_PT,
                             placement.width_mm * MM_TO_PT,
                             placement.height_mm * MM_TO_PT,
                             preserveAspectRatio=True, anchor="c", mask="auto")
            if request.cutting_guides:
                gap = min(max(request.layout.spacing_mm / 3, 0.3), 1.0) * MM_TO_PT
                x = placement.x_mm * MM_TO_PT
                y = (layout.paper_height_mm - placement.y_mm -
                     placement.height_mm) * MM_TO_PT
                w, h = placement.width_mm * MM_TO_PT, placement.height_mm * MM_TO_PT
                canvas.setLineWidth(0.25)
                canvas.line(x-gap, y, x, y); canvas.line(x, y-gap, x, y)
                canvas.line(x+w, y-gap, x+w, y); canvas.line(x+w, y, x+w+gap, y)
                canvas.line(x-gap, y+h, x, y+h); canvas.line(x, y+h, x, y+h+gap)
                canvas.line(x+w, y+h, x+w+gap, y+h); canvas.line(x+w, y+h, x+w, y+h+gap)
        canvas.showPage()
        canvas.save()
        return ExportResult(output.getvalue(), "application/pdf", "photo-sheet.pdf")
    if fmt not in {"PNG", "JPG", "JPEG"}:
        raise PhotoScpecError("unsupported_export_format", "Sheet format must be PDF, PNG, or JPG")
    width_px = int(math.floor(layout.paper_width_mm * request.dpi / 25.4 + 0.5))
    height_px = int(math.floor(layout.paper_height_mm * request.dpi / 25.4 + 0.5))
    if width_px * height_px > MAX_SHEET_PIXELS:
        raise PhotoScpecError("resource_limit", "Raster sheet exceeds the pixel limit")
    sheet = Image.new("RGB", (width_px, height_px), "white")
    for placement in layout.positions:
        rendered = photo.rotate(-90, expand=True) if placement.rotated else photo
        left = int(math.floor(placement.x_mm * request.dpi / 25.4 + 0.5))
        top = int(math.floor(placement.y_mm * request.dpi / 25.4 + 0.5))
        right = int(math.floor((placement.x_mm + placement.width_mm)
                               * request.dpi / 25.4 + 0.5))
        bottom = int(math.floor((placement.y_mm + placement.height_mm)
                                * request.dpi / 25.4 + 0.5))
        rendered = rendered.resize((right-left, bottom-top), Image.Resampling.LANCZOS)
        sheet.paste(rendered, (left, top))
    return _encode(sheet, fmt, request.dpi)
