"""Photo validation."""
from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import ValidationRequest, ValidationResult
from ._image import open_image


def validate_photo(request: ValidationRequest) -> ValidationResult:
    if (not isinstance(request.width_px, int) or not isinstance(request.height_px, int)
            or isinstance(request.width_px, bool) or isinstance(request.height_px, bool)
            or request.width_px <= 0 or request.height_px <= 0):
        raise PhotoScpecError("INVALID_DIMENSIONS",
                              "Required dimensions must be positive integers")
    image = open_image(request.image)
    warnings = []
    if image.width != request.width_px or image.height != request.height_px:
        warnings.append(
            f"Image is {image.width}x{image.height}px; exactly "
            f"{request.width_px}x{request.height_px}px is required"
        )
    return ValidationResult(not warnings, warnings)
