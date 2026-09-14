"""Physical and pixel dimension conversion."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import DimensionsRequest, DimensionsResult

MAX_SIDE_PX = 100_000


def _positive(value: float, name: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        number = Decimal("NaN")
    if not number.is_finite() or number <= 0:
        raise PhotoScpecError("INVALID_DIMENSIONS", f"{name} must be finite and positive",
                              {"field": name})
    return number


def resolve_dimensions(request: DimensionsRequest) -> DimensionsResult:
    width = _positive(request.width, "width")
    height = _positive(request.height, "height")
    if isinstance(request.dpi, bool) or not isinstance(request.dpi, int) or not 1 <= request.dpi <= 2400:
        raise PhotoScpecError("INVALID_DPI", "DPI must be an integer from 1 to 2400")
    if not isinstance(request.unit, str):
        raise PhotoScpecError("INVALID_DIMENSIONS", "Unit must be mm, inch, or px")
    unit = request.unit.lower()
    if unit == "mm":
        width_mm, height_mm = width, height
    elif unit in {"inch", "in"}:
        width_mm, height_mm = width * Decimal("25.4"), height * Decimal("25.4")
    elif unit == "px":
        if width != width.to_integral_value() or height != height.to_integral_value():
            raise PhotoScpecError("INVALID_DIMENSIONS", "Pixel dimensions must be whole numbers")
        width_mm = width * Decimal("25.4") / request.dpi
        height_mm = height * Decimal("25.4") / request.dpi
    else:
        raise PhotoScpecError("INVALID_DIMENSIONS", "Unit must be mm, inch, in, or px",
                              {"unit": request.unit})
    width_px = int((width_mm * request.dpi / Decimal("25.4")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP))
    height_px = int((height_mm * request.dpi / Decimal("25.4")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP))
    if min(width_px, height_px) < 1 or max(width_px, height_px) > MAX_SIDE_PX:
        raise PhotoScpecError("INVALID_DIMENSIONS",
                              "Resolved pixel dimensions are out of bounds",
                              {"max_side_px": MAX_SIDE_PX})
    return DimensionsResult(float(width_mm), float(height_mm), width_px, height_px, request.dpi)
