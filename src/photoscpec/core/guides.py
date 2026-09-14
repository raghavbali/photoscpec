"""Translate optional specification metadata to normalized composition guides."""
from photoscpec.config.models import PhotoSpec
from photoscpec.interfaces.models import Guide, GuideResult


def _line(enabled: bool, guide_id: str, position: float | None) -> Guide | None:
    if not enabled or position is None:
        return None
    return Guide(type="horizontal", id=guide_id, position=float(position))


def get_guides(spec: PhotoSpec | None) -> GuideResult:
    """Return top-left-origin normalized aids; these do not guarantee acceptance."""
    if spec is None:
        return GuideResult(guides=[])
    data = spec.guides
    if not data:
        return GuideResult(
            guides=[
                Guide(type="vertical", id="generic-composition-center", position=0.5),
                Guide(type="horizontal", id="generic-composition-eye-line", position=0.4),
                Guide(
                    type="rectangle",
                    id="generic-composition-head-region",
                    x=0.2,
                    y=0.1,
                    width=0.6,
                    height=0.8,
                ),
            ]
        )

    result: list[Guide] = []
    if data.get("center_line", False):
        result.append(Guide(type="vertical", id="center-line", position=0.5))
    eye = data.get("eye_line") or {}
    item = _line(eye.get("enabled", False), "eye-line", eye.get("position_ratio"))
    if item:
        result.append(item)
    face_eye = spec.face.get("eye_line_ratio")
    if eye.get("enabled", False) and eye.get("position_ratio") is None and face_eye is not None:
        result.append(Guide(type="horizontal", id="eye-line", position=float(face_eye)))
    for key, guide_id, fallback in (
        ("crown_line", "crown-line", 0.1),
        ("chin_line", "chin-line", 0.8),
    ):
        item_data = data.get(key) or {}
        item = _line(item_data.get("enabled", False), guide_id, item_data.get("position_ratio", fallback))
        if item:
            result.append(item)
    region = data.get("head_region") or {}
    if region.get("enabled", False) and all(
        key in region for key in ("x", "y", "width", "height")
    ):
        result.append(
            Guide(
                type="rectangle",
                id="head-region",
                x=float(region["x"]),
                y=float(region["y"]),
                width=float(region["width"]),
                height=float(region["height"]),
            )
        )
    return GuideResult(guides=result)
