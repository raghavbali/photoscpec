"""Physical and pixel dimension conversion."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import DimensionsRequest, DimensionsResult

MAX_SIDE_PX = 100_000


def _positive(value: float, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        number = Decimal("NaN")
    if not number.is_finite() or number <= 0:
        raise PhotoScpecError("invalid_dimensions", f"{name} must be finite and positive",
                              {"field": name})
    return number


def resolve_dimensions(request: DimensionsRequest) -> DimensionsResult:
    width = _positive(request.width, "width")
    height = _positive(request.height, "height")
    if isinstance(request.dpi, bool) or not isinstance(request.dpi, int) or request.dpi <= 0:
        raise PhotoScpecError("invalid_dpi", "DPI must be a positive integer")
    unit = request.unit.lower()
    if unit == "mm":
        width_mm, height_mm = width, height
    elif unit in {"inch", "in"}:
        width_mm, height_mm = width * Decimal("25.4"), height * Decimal("25.4")
    elif unit == "px":
        width_mm = width * Decimal("25.4") / request.dpi
        height_mm = height * Decimal("25.4") / request.dpi
    else:
        raise PhotoScpecError("invalid_unit", "Unit must be mm, inch, in, or px",
                              {"unit": request.unit})
    width_px = int((width_mm * request.dpi / Decimal("25.4")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP))
    height_px = int((height_mm * request.dpi / Decimal("25.4")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP))
    if min(width_px, height_px) < 1 or max(width_px, height_px) > MAX_SIDE_PX:
        raise PhotoScpecError("invalid_dimensions", "Resolved pixel dimensions are out of bounds",
                              {"max_side_px": MAX_SIDE_PX})
    return DimensionsResult(float(width_mm), float(height_mm), width_px, height_px, request.dpi)
