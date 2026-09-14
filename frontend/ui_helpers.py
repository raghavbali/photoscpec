"""Pure presentation helpers used by the Streamlit adapter."""
from __future__ import annotations

from io import BytesIO
from typing import MutableMapping

from PIL import Image, ImageDraw

from photoscpec.interfaces.models import CropFrameRequest, Guide, LayoutRequest

PAPERS_MM = {
    "4 × 6 in": (101.6, 152.4),
    "5 × 7 in": (127.0, 177.8),
    "6 × 8 in": (152.4, 203.2),
    "A4": (210.0, 297.0),
    "Letter": (215.9, 279.4),
}
GRID_SHAPES = {
    "2 × 2": (2, 2), "2 × 3": (2, 3), "2 × 4": (2, 4),
    "2 × 6": (2, 6), "3 × 4": (3, 4), "4 × 4": (4, 4),
}


def keep_ratio_from_width(state: MutableMapping[str, object]) -> None:
    ratio = float(state.get("custom_ratio", 1.0))
    if ratio > 0:
        state["custom_height"] = round(float(state["custom_width"]) / ratio, 4)


def keep_ratio_from_height(state: MutableMapping[str, object]) -> None:
    ratio = float(state.get("custom_ratio", 1.0))
    if ratio > 0:
        state["custom_width"] = round(float(state["custom_height"]) * ratio, 4)


def crop_frame_request(image: bytes, width_px: int, height_px: int, state) -> CropFrameRequest:
    return CropFrameRequest(
        image=image, output_width_px=width_px, output_height_px=height_px,
        zoom=float(state["zoom"]), pan_x=float(state["pan_x"]), pan_y=float(state["pan_y"]),
        rotation_degrees=int(state["rotation"]),
    )


def layout_request(photo_width_mm: float, photo_height_mm: float, paper: tuple[float, float],
                   copies: int, spacing: float, margin: float, grid: str,
                   rows: int | None, columns: int | None, orientation: str | None) -> LayoutRequest:
    if grid == "Auto":
        rows = columns = None
        mode = "auto"
    else:
        if grid in GRID_SHAPES:
            rows, columns = GRID_SHAPES[grid]
        mode = "custom"
    return LayoutRequest(
        photo_width_mm=photo_width_mm, photo_height_mm=photo_height_mm,
        paper_width_mm=paper[0], paper_height_mm=paper[1], copies=copies,
        spacing_mm=spacing, margin_mm=margin, layout_mode=mode, orientation=orientation,
        rows=rows, columns=columns, allow_rotate=True,
    )


def guide_preview(image_bytes: bytes, guides: list[Guide]) -> bytes:
    """Draw normalized service guides onto a display-only copy."""
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size
    stroke = max(1, round(min(width, height) / 250))
    for guide in guides:
        color = (20, 220, 120)
        if guide.type in {"horizontal", "line_y"} and guide.position is not None:
            y = round(guide.position * height)
            draw.line((0, y, width, y), fill=color, width=stroke)
        elif guide.type in {"vertical", "line_x"} and guide.position is not None:
            x = round(guide.position * width)
            draw.line((x, 0, x, height), fill=color, width=stroke)
        elif None not in (guide.x, guide.y, guide.width, guide.height):
            box = (round(guide.x * width), round(guide.y * height),
                   round((guide.x + guide.width) * width), round((guide.y + guide.height) * height))
            if guide.type in {"ellipse", "oval", "face"}:
                draw.ellipse(box, outline=color, width=stroke)
            else:
                draw.rectangle(box, outline=color, width=stroke)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
