from dataclasses import asdict
from io import BytesIO
import json

from PIL import Image
from pypdf import PdfReader
import pytest

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import (
    CropFrameRequest, CropRequest, DimensionsRequest, GuideRequest,
    LayoutRequest, PhotoExportRequest, SheetExportRequest, ValidationRequest,
)
from photoscpec.services.photoscpec_service import PhotoScpecService


def portrait():
    image = Image.new("RGB", (700, 900), "navy")
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def test_headless_photo_to_print_workflow():
    service = PhotoScpecService()
    assert not service.config_errors
    spec = service.get_spec("india_birth_registration")
    size = service.resolve_dimensions(DimensionsRequest(spec.width_mm, spec.height_mm))
    assert (size.width_px, size.height_px) == (413, 531)
    source = portrait()
    frame = service.calculate_crop(CropFrameRequest(source, size.width_px, size.height_px))
    photo = service.create_crop(CropRequest(source, frame, size.width_px, size.height_px))
    assert service.validate_photo(ValidationRequest(photo.image, 413, 531)).valid
    guides = service.get_guides(GuideRequest(spec.id))
    assert guides.guides
    json.dumps(asdict(guides))
    layout = LayoutRequest(35, 45, 210, 297, copies=7)
    result = service.calculate_layout(layout)
    assert result.copies_rendered == len(result.positions) == 7
    assert result.capacity > 7
    for fmt in ("PNG", "JPG"):
        exported = service.export_photo(PhotoExportRequest(photo.image, fmt))
        assert Image.open(BytesIO(exported.data)).size == (413, 531)
        if fmt == "PNG":
            assert Image.open(BytesIO(exported.data)).getpixel((200, 200)) == (0, 0, 128)
    pdf = service.export_sheet(SheetExportRequest(photo.image, layout))
    page = PdfReader(BytesIO(pdf.data)).pages[0]
    assert float(page.mediabox.width) == pytest.approx(result.paper_width_mm / 25.4 * 72, abs=0.01)


def test_digital_dimensions_and_errors():
    service = PhotoScpecService()
    size = service.resolve_dimensions(DimensionsRequest(630, 810, "px", 300))
    assert (size.width_px, size.height_px) == (630, 810)
    with pytest.raises(PhotoScpecError) as error:
        service.get_spec("does-not-exist")
    assert error.value.code == "SPEC_NOT_FOUND"
    with pytest.raises(PhotoScpecError) as error:
        service.calculate_layout(LayoutRequest(35, 45, 101.6, 152.4, copies=8))
    assert error.value.code == "LAYOUT_DOES_NOT_FIT"


def test_empty_catalog_still_supports_custom(tmp_path):
    service = PhotoScpecService(tmp_path)
    assert service.list_specs() == []
    assert service.resolve_dimensions(DimensionsRequest(2, 2, "inch")).width_px == 600
