"""Image inspection and aspect-preserving cropping.

Rotation is clockwise and is applied after EXIF orientation normalization.
"""
from io import BytesIO
import math

from PIL import Image

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import (
    CropFrameRequest, CropRect, CropRequest, CropResult, ImageInfo,
)
from ._image import open_image, rgb_on_white

_RESAMPLE = Image.Resampling.LANCZOS
MAX_OUTPUT_PIXELS = 100_000_000


def _rotation(value: int) -> int:
    if value not in {0, 90, 180, 270}:
        raise PhotoScpecError("invalid_rotation", "Rotation must be 0, 90, 180, or 270")
    return value


def _rotated(image: Image.Image, degrees: int) -> Image.Image:
    return image.rotate(-_rotation(degrees), expand=True)


def _output_size(width: int, height: int) -> None:
    if (isinstance(width, bool) or isinstance(height, bool) or not isinstance(width, int)
            or not isinstance(height, int) or width <= 0 or height <= 0
            or width * height > MAX_OUTPUT_PIXELS):
        raise PhotoScpecError("invalid_output_size", "Output dimensions are out of bounds")


def inspect_image(data: bytes) -> ImageInfo:
    image = open_image(data)
    orientation = "landscape" if image.width > image.height else (
        "portrait" if image.height > image.width else "square")
    return ImageInfo(image.width, image.height, image.format, orientation,
                     image.width / image.height)


def calculate_crop(request: CropFrameRequest) -> CropRect:
    _output_size(request.output_width_px, request.output_height_px)
    if not math.isfinite(request.zoom) or request.zoom < 1:
        raise PhotoScpecError("invalid_zoom", "Zoom must be finite and at least 1")
    if (not math.isfinite(request.pan_x) or not math.isfinite(request.pan_y)
            or not 0 <= request.pan_x <= 1 or not 0 <= request.pan_y <= 1):
        raise PhotoScpecError("invalid_pan", "Pan coordinates must be between 0 and 1")
    image = _rotated(open_image(request.image), request.rotation_degrees)
    target = request.output_width_px / request.output_height_px
    if image.width / image.height >= target:
        base_h = float(image.height)
        base_w = base_h * target
    else:
        base_w = float(image.width)
        base_h = base_w / target
    crop_w, crop_h = base_w / request.zoom, base_h / request.zoom
    x = (image.width - crop_w) * request.pan_x
    y = (image.height - crop_h) * request.pan_y
    return CropRect(x, y, crop_w, crop_h)


def create_crop(request: CropRequest) -> CropResult:
    _output_size(request.output_width_px, request.output_height_px)
    image = _rotated(open_image(request.image), request.rotation_degrees)
    values = (request.crop.x, request.crop.y, request.crop.width, request.crop.height)
    if not all(math.isfinite(v) for v in values) or request.crop.width <= 0 or request.crop.height <= 0:
        raise PhotoScpecError("invalid_crop", "Crop rectangle must be finite and positive")
    if (request.crop.x < 0 or request.crop.y < 0
            or request.crop.x + request.crop.width > image.width + 1e-6
            or request.crop.y + request.crop.height > image.height + 1e-6):
        raise PhotoScpecError("invalid_crop", "Crop rectangle falls outside the image")
    actual = request.crop.width / request.crop.height
    expected = request.output_width_px / request.output_height_px
    tolerance = max(1 / request.output_width_px, 1 / request.output_height_px)
    if abs(actual / expected - 1) > tolerance:
        raise PhotoScpecError("crop_aspect_mismatch", "Crop aspect ratio does not match output")
    box = (request.crop.x, request.crop.y, request.crop.x + request.crop.width,
           request.crop.y + request.crop.height)
    rendered = rgb_on_white(image.crop(box)).resize(
        (request.output_width_px, request.output_height_px), _RESAMPLE)
    output = BytesIO()
    rendered.save(output, "PNG", optimize=True)
    return CropResult(output.getvalue(), rendered.width, rendered.height)
