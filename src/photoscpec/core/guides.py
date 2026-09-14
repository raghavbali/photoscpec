"""Translate optional specification guide metadata to public guide contracts."""
from photoscpec.config.models import PhotoSpec
from photoscpec.interfaces.models import Guide, GuideResult


def get_guides(spec: PhotoSpec | None) -> GuideResult:
    if spec is None:
        return GuideResult(guides=[])
    data = spec.guides
    guides: list[Guide] = []
    for key, guide_id in (
        ("eye_line_ratio", "eye-line"),
        ("chin_line_ratio", "chin-line"),
        ("crown_line_ratio", "crown-line"),
    ):
        if key in data:
            guides.append(
                Guide(type="horizontal", id=guide_id, position=float(data[key]))
            )
    for key, guide_id in (("face_bounds", "face-bounds"), ("safe_area", "safe-area")):
        bounds = data.get(key)
        if isinstance(bounds, dict):
            guides.append(
                Guide(
                    type="rectangle",
                    id=guide_id,
                    x=float(bounds["x"]),
                    y=float(bounds["y"]),
                    width=float(bounds["width"]),
                    height=float(bounds["height"]),
                )
            )
    return GuideResult(guides=guides)
