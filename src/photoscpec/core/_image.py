"""Bounded image decoding helpers."""
from io import BytesIO
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from photoscpec.interfaces.errors import PhotoScpecError

MAX_INPUT_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 100_000_000
_ALLOWED = {"JPEG", "PNG"}


def open_image(data: bytes) -> Image.Image:
    if not isinstance(data, bytes) or not data:
        raise PhotoScpecError("UNSUPPORTED_IMAGE", "Image data must be non-empty bytes")
    if len(data) > MAX_INPUT_BYTES:
        raise PhotoScpecError("UNSUPPORTED_IMAGE", "Image file exceeds the 50 MiB limit",
                              {"max_bytes": MAX_INPUT_BYTES})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            source = Image.open(BytesIO(data))
            fmt = source.format
            if fmt not in _ALLOWED:
                raise PhotoScpecError("UNSUPPORTED_IMAGE", "Only JPG and PNG images are supported",
                                      {"format": fmt})
            source.verify()
            image = Image.open(BytesIO(data))
            if image.width * image.height > MAX_PIXELS:
                raise PhotoScpecError("UNSUPPORTED_IMAGE",
                                      "Image dimensions exceed the pixel limit",
                                      {"max_pixels": MAX_PIXELS})
            image.load()
    except PhotoScpecError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise PhotoScpecError("UNSUPPORTED_IMAGE", "Image could not be decoded") from exc
    image = ImageOps.exif_transpose(image)
    image.format = fmt
    return image


def rgb_on_white(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = Image.new("RGBA", rgba.size, "white")
    background.alpha_composite(rgba)
    return background.convert("RGB")
