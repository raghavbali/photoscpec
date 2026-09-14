from photoscpec.config.models import PhotoSpec
from photoscpec.core.guides import get_guides


def _spec(**values):
    return PhotoSpec(
        id="x",
        name="X",
        category="custom",
        country_id="XX",
        country_name="Example",
        width_mm=35,
        height_mm=45,
        default_dpi=300,
        **values,
    )


def test_canonical_toggles_are_honored():
    spec = _spec(
        guides={
            "center_line": True,
            "eye_line": {"enabled": True, "position_ratio": 0.4},
            "crown_line": {"enabled": False},
            "chin_line": {"enabled": True},
            "head_region": {
                "enabled": True,
                "x": 0.2,
                "y": 0.1,
                "width": 0.6,
                "height": 0.8,
            },
        }
    )
    assert [guide.id for guide in get_guides(spec).guides] == [
        "center-line",
        "eye-line",
        "chin-line",
        "head-region",
    ]


def test_custom_spec_and_none_get_generic_composition_aids():
    assert [guide.id for guide in get_guides(_spec()).guides] == [
        "generic-composition-center",
        "generic-composition-eye-line",
        "generic-composition-head-region",
    ]
    assert get_guides(None).guides == get_guides(_spec()).guides
