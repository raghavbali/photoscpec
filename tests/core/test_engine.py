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
    CropFrameRequest, CropRect, CropRequest, DimensionsRequest, LayoutRequest,
    PhotoExportRequest, SheetExportRequest, ValidationRequest,
)


def picture(size=(400, 300), mode="RGB", fmt="PNG", color="red"):
    fill = (255, 0, 0, 128) if mode == "RGBA" else color
    image = Image.new(mode, size, fill)
    output = BytesIO()
    image.save(output, fmt)
    return output.getvalue()


def split_picture():
    image = Image.new("RGB", (400, 200), "red")
    ImageDraw = __import__("PIL.ImageDraw", fromlist=["ImageDraw"])
    ImageDraw.Draw(image).rectangle((200, 0, 399, 199), fill="blue")
    output = BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def test_dimensions_use_physical_units_and_half_up_rounding():
    result = resolve_dimensions(DimensionsRequest(35, 45, "mm", 300))
    assert (result.width_px, result.height_px) == (413, 531)
    inches = resolve_dimensions(DimensionsRequest(1, 2, "inch", 300))
    assert (inches.width_mm, inches.height_px) == (25.4, 600)


@pytest.mark.parametrize("bad", [0, -1, float("inf"), float("nan")])
def test_dimensions_reject_invalid_values(bad):
    with pytest.raises(PhotoScpecError) as exc:
        resolve_dimensions(DimensionsRequest(bad, 45))
    assert exc.value.code == "INVALID_DIMENSIONS"


def test_crop_coordinates_are_normalized_and_select_visible_region():
    data = split_picture()
    frame = calculate_crop(CropFrameRequest(data, 100, 100, pan_x=1))
    assert all(0 <= value <= 1 for value in (
        frame.x, frame.y, frame.width, frame.height))
    assert frame == CropRect(.5, 0, .5, 1)
    result = create_crop(CropRequest(data, frame, 100, 100))
    with Image.open(BytesIO(result.image)) as image:
        assert image.getpixel((50, 50)) == (0, 0, 255)


def test_crop_rejects_normalized_overflow_and_extreme_zoom():
    data = picture()
    with pytest.raises(PhotoScpecError) as exc:
        create_crop(CropRequest(data, CropRect(.8, 0, .3, .5), 3, 5))
    assert exc.value.code == "INVALID_CROP"
    with pytest.raises(PhotoScpecError):
        calculate_crop(CropFrameRequest(data, 10, 10, zoom=1000))


def test_crop_warns_when_upscaling():
    data = picture((10, 10))
    frame = calculate_crop(CropFrameRequest(data, 100, 100))
    assert create_crop(CropRequest(data, frame, 100, 100)).warnings


def test_alpha_is_composited_on_white():
    result = export_photo(PhotoExportRequest(picture((10, 10), "RGBA")))
    with Image.open(BytesIO(result.data)) as image:
        assert image.convert("RGB").getpixel((0, 0)) == (255, 127, 127)


def test_inspection_and_exact_validation():
    data = picture((400, 300), fmt="JPEG")
    assert inspect_image(data).format == "JPEG"
    assert validate_photo(ValidationRequest(data, 400, 300)).valid
    assert not validate_photo(ValidationRequest(data, 300, 200)).valid


def test_auto_layout_maximizes_capacity():
    layout = calculate_layout(LayoutRequest(35, 45, 210, 297, 1))
    capacities = []
    for orientation in ("portrait", "landscape"):
        for allow_rotate in (False,):
            candidate = calculate_layout(LayoutRequest(
                35, 45, 210, 297, 1, orientation=orientation,
                allow_rotate=allow_rotate))
            capacities.append(candidate.capacity)
    assert layout.capacity >= max(capacities)


@pytest.mark.parametrize("copies", [1, 2, 6])
def test_four_by_six_layout_supported_counts(copies):
    layout = calculate_layout(LayoutRequest(35, 45, 101.6, 152.4, copies))
    assert layout.copies_rendered == copies
    assert len(layout.positions) == copies
    assert layout.capacity >= copies


def test_geometric_capacity_is_six_not_eight():
    with pytest.raises(PhotoScpecError) as exc:
        calculate_layout(LayoutRequest(35, 45, 101.6, 152.4, 8))
    assert exc.value.code == "LAYOUT_DOES_NOT_FIT"
    assert exc.value.details["maximum_capacity"] == 6


@pytest.mark.parametrize("copies", [7, 8, 12, 16])
def test_larger_sheet_exact_copy_counts(copies):
    layout = calculate_layout(LayoutRequest(35, 45, 210, 297, copies))
    assert len(layout.positions) == copies


def test_explicit_grid_does_not_fill_unused_cells():
    layout = calculate_layout(LayoutRequest(
        35, 45, 210, 297, 7, layout_mode="grid", rows=4, columns=4))
    assert layout.capacity == 16
    assert len(layout.positions) == 7


def test_pdf_physical_page_geometry_and_single_page():
    data = picture((350, 450))
    request = SheetExportRequest(
        data, LayoutRequest(35, 45, 101.6, 152.4, 2), cutting_guides=True)
    result = export_sheet(request)
    reader = PdfReader(BytesIO(result.data))
    assert len(reader.pages) == 1
    page = reader.pages[0]
    assert float(page.mediabox.width) == pytest.approx(101.6 * 72 / 25.4, abs=.02)
    assert float(page.mediabox.height) == pytest.approx(152.4 * 72 / 25.4, abs=.02)


def test_sheet_rejects_unrelated_aspect():
    with pytest.raises(PhotoScpecError) as exc:
        export_sheet(SheetExportRequest(
            picture((400, 300)), LayoutRequest(35, 45, 101.6, 152.4, 1)))
    assert exc.value.code == "EXPORT_FAILED"


def test_zero_spacing_guides_are_safely_skipped():
    request = SheetExportRequest(
        picture((350, 450)), LayoutRequest(35, 45, 70, 45, 2, spacing_mm=0,
                                          margin_mm=0, allow_rotate=False),
        format="PNG", dpi=100, cutting_guides=True)
    result = export_sheet(request)
    with Image.open(BytesIO(result.data)) as image:
        assert image.size == (276, 177)
