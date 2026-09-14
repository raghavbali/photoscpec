from photoscpec.config.models import PhotoSpec
from photoscpec.core.guides import get_guides


def test_guides_use_normalized_top_left_values():
    spec = PhotoSpec(
        id="x",
        name="X",
        category="passport",
        country_id="XX",
        country_name="Example",
        width_mm=35,
        height_mm=45,
        default_dpi=300,
        guides={
            "eye_line_ratio": 0.4,
            "face_bounds": {"x": 0.2, "y": 0.1, "width": 0.6, "height": 0.8},
        },
    )
    result = get_guides(spec)
    assert result.guides[0].position == 0.4
    assert (result.guides[1].x, result.guides[1].y) == (0.2, 0.1)


def test_no_spec_has_no_guides():
    assert get_guides(None).guides == []
