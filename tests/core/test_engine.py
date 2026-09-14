from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfReader

from photoscpec.core.crop import calculate_crop, create_crop, inspect_image
from photoscpec.core.dimensions import resolve_dimensions
from photoscpec.core.export import export_photo, export_sheet
from photoscpec.core.layout import calculate_layout
from photoscpec.core.validation import validate_photo
from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import (
    CropFrameRequest, CropRequest, DimensionsRequest, LayoutRequest,
    PhotoExportRequest, SheetExportRequest, ValidationRequest,
)


def picture(size=(400, 300), mode="RGB", fmt="PNG"):
    image = Image.new(mode, size, (255, 0, 0, 128) if mode == "RGBA" else "red")
    output = BytesIO()
    image.save(output, fmt)
    return output.getvalue()


def test_dimensions_use_physical_units_and_half_up_rounding():
    result = resolve_dimensions(DimensionsRequest(35, 45, "mm", 300))
    assert (result.width_px, result.height_px) == (413, 531)
    inches = resolve_dimensions(DimensionsRequest(1, 2, "inch", 300))
    assert (inches.width_mm, inches.height_px) == (25.4, 600)


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan")])
def test_dimensions_reject_invalid_values(bad):
    with pytest.raises(PhotoScpecError):
        resolve_dimensions(DimensionsRequest(bad, 45))


def test_crop_is_aspect_correct_and_png_metadata_free():
    data = picture()
    frame = calculate_crop(CropFrameRequest(data, 200, 200, zoom=2, pan_x=1, pan_y=0))
    assert frame.width == frame.height == 150
    assert frame.x == 250 and frame.y == 0
    result = create_crop(CropRequest(data, frame, 200, 200))
    with Image.open(BytesIO(result.image)) as image:
        assert image.format == "PNG"
        assert image.size == (200, 200)
        assert not image.info


def test_alpha_is_composited_on_white():
    result = export_photo(PhotoExportRequest(picture((10, 10), "RGBA")))
    with Image.open(BytesIO(result.data)) as image:
        assert image.convert("RGB").getpixel((0, 0)) == (255, 127, 127)


def test_inspection_and_validation():
    data = picture((400, 300), fmt="JPEG")
    assert inspect_image(data).format == "JPEG"
    assert validate_photo(ValidationRequest(data, 300, 200)).valid
    assert not validate_photo(ValidationRequest(data, 500, 200)).valid


@pytest.mark.parametrize("copies", [1, 2, 6])
def test_four_by_six_layout_supported_counts(copies):
    layout = calculate_layout(LayoutRequest(35, 45, 101.6, 152.4, copies))
    assert layout.copies_rendered == copies
    assert len(layout.positions) == copies
    assert layout.capacity >= copies


def test_geometric_capacity_is_six_not_eight():
    with pytest.raises(PhotoScpecError) as exc:
        calculate_layout(LayoutRequest(35, 45, 101.6, 152.4, 8))
    assert exc.value.code == "insufficient_capacity"
    assert exc.value.details["maximum_capacity"] == 6


@pytest.mark.parametrize("copies", [7, 8, 12, 16])
def test_larger_sheet_exact_copy_counts(copies):
    layout = calculate_layout(LayoutRequest(35, 45, 210, 297, copies))
    assert len(layout.positions) == copies
    assert layout.copies_rendered == copies


def test_explicit_grid_does_not_fill_unused_cells():
    layout = calculate_layout(LayoutRequest(
        35, 45, 210, 297, 7, layout_mode="grid", rows=4, columns=4))
    assert layout.capacity == 16
    assert len(layout.positions) == 7


def test_pdf_physical_page_geometry_and_single_page():
    request = SheetExportRequest(
        picture(), LayoutRequest(35, 45, 101.6, 152.4, 2), cutting_guides=True)
    result = export_sheet(request)
    reader = PdfReader(BytesIO(result.data))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(101.6 * 72 / 25.4, abs=.02)
    assert float(page.mediabox.height) == pytest.approx(152.4 * 72 / 25.4, abs=.02)


def test_invalid_crop_ratio_and_format_are_rejected():
    data = picture()
    with pytest.raises(PhotoScpecError, match="aspect"):
        create_crop(CropRequest(data, calculate_crop(
            CropFrameRequest(data, 200, 200)), 100, 200))
    with pytest.raises(PhotoScpecError):
        inspect_image(b"not an image")
