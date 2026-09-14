"""Public contracts. Coordinates use top-left origin; print geometry uses mm."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CropRect:
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class DimensionsRequest:
    width: float
    height: float
    unit: str = "mm"
    dpi: int = 300


@dataclass(frozen=True)
class DimensionsResult:
    width_mm: float
    height_mm: float
    width_px: int
    height_px: int
    dpi: int


@dataclass(frozen=True)
class ImageInfo:
    width_px: int
    height_px: int
    format: str
    orientation: str
    aspect_ratio: float


@dataclass(frozen=True)
class CropFrameRequest:
    image: bytes
    output_width_px: int
    output_height_px: int
    zoom: float = 1.0
    pan_x: float = 0.5
    pan_y: float = 0.5
    rotation_degrees: int = 0


@dataclass(frozen=True)
class CropRequest:
    image: bytes
    crop: CropRect
    output_width_px: int
    output_height_px: int
    rotation_degrees: int = 0


@dataclass(frozen=True)
class CropResult:
    image: bytes
    width_px: int
    height_px: int
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Guide:
    type: str
    id: str
    position: float | None = None
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None


@dataclass(frozen=True)
class GuideRequest:
    spec_id: str | None = None


@dataclass(frozen=True)
class GuideResult:
    guides: list[Guide]


@dataclass(frozen=True)
class ValidationRequest:
    image: bytes
    width_px: int
    height_px: int


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class LayoutRequest:
    photo_width_mm: float
    photo_height_mm: float
    paper_width_mm: float
    paper_height_mm: float
    copies: int
    spacing_mm: float = 2
    margin_mm: float = 3
    layout_mode: str = "auto"
    orientation: str | None = None
    rows: int | None = None
    columns: int | None = None
    allow_rotate: bool = True


@dataclass(frozen=True)
class PhotoPlacement:
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float
    rotated: bool = False


@dataclass(frozen=True)
class LayoutResult:
    rows: int
    columns: int
    capacity: int
    copies_rendered: int
    orientation: str
    paper_width_mm: float
    paper_height_mm: float
    positions: list[PhotoPlacement]
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PhotoExportRequest:
    image: bytes
    format: str = "PNG"
    dpi: int = 300


@dataclass(frozen=True)
class SheetExportRequest:
    image: bytes
    layout: LayoutRequest
    format: str = "PDF"
    dpi: int = 300
    cutting_guides: bool = False


@dataclass(frozen=True)
class ExportResult:
    data: bytes
    mime_type: str
    filename: str
