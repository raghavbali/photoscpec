"""Stateless photo operations and configuration catalog; no image retention."""
from pathlib import Path

from photoscpec.config.loader import load_specs
from photoscpec.core import crop, dimensions, export, guides, layout, validation
from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import (
    CropFrameRequest, CropRect, CropRequest, CropResult,
    DimensionsRequest, DimensionsResult, ExportResult,
    GuideRequest, GuideResult, ImageInfo, LayoutRequest, LayoutResult,
    PhotoExportRequest, SheetExportRequest, ValidationRequest, ValidationResult,
)


class PhotoScpecService:
    def __init__(self, config_dir: str | Path | None = None):
        directory = Path(config_dir) if config_dir is not None else (
            Path(__file__).resolve().parents[3] / "configs"
        )
        loaded = load_specs(directory)
        self._specs = {spec.id: spec for spec in loaded.specs}
        self.config_errors = loaded.errors

    def list_specs(self):
        return list(self._specs.values())

    def get_spec(self, spec_id: str):
        try:
            return self._specs[spec_id]
        except (KeyError, TypeError) as exc:
            raise PhotoScpecError("SPEC_NOT_FOUND", f"Unknown specification: {spec_id}") from exc

    def resolve_dimensions(self, request: DimensionsRequest) -> DimensionsResult:
        return dimensions.resolve_dimensions(request)

    def inspect_image(self, image: bytes) -> ImageInfo:
        return crop.inspect_image(image)

    def calculate_crop(self, request: CropFrameRequest) -> CropRect:
        return crop.calculate_crop(request)

    def create_crop(self, request: CropRequest) -> CropResult:
        return crop.create_crop(request)

    def get_guides(self, request: GuideRequest) -> GuideResult:
        spec = self.get_spec(request.spec_id) if request.spec_id is not None else None
        return guides.get_guides(spec)

    def validate_photo(self, request: ValidationRequest) -> ValidationResult:
        return validation.validate_photo(request)

    def calculate_layout(self, request: LayoutRequest) -> LayoutResult:
        return layout.calculate_layout(request)

    def export_photo(self, request: PhotoExportRequest) -> ExportResult:
        return export.export_photo(request)

    def export_sheet(self, request: SheetExportRequest) -> ExportResult:
        return export.export_sheet(request)
