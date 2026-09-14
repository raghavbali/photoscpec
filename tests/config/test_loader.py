from pathlib import Path

from photoscpec.config import load_specs


def _document(format_body: str, country: str = "AA") -> str:
    return f"country:\n  id: {country}\nformats:\n{format_body}"


def test_loads_canonical_schema_and_defaults(tmp_path: Path):
    (tmp_path / "a.yaml").write_text(
        _document("  - id: a\n    photo: {width_mm: 35, height_mm: 45}\n")
    )
    (tmp_path / "b.yml").write_text(
        _document(
            "  - id: b\n    name: Visa B\n    category: visa\n"
            "    photo: {width_mm: 50.8, height_mm: 50.8, default_dpi: 600}\n",
            "BB",
        )
    )
    result = load_specs(tmp_path)
    assert [(s.id, s.name, s.category, s.default_dpi) for s in result.specs] == [
        ("a", "a", "custom", 300),
        ("b", "Visa B", "visa", 600),
    ]
    assert result.specs[0].country_name == "AA"
    assert result.errors == []


def test_malformed_yaml_and_invalid_encoding_do_not_hide_valid_file(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text("formats: [")
    (tmp_path / "encoding.yml").write_bytes(b"\xff\xfe")
    (tmp_path / "good.yaml").write_text(
        _document("  - id: good\n    photo: {width_mm: 35, height_mm: 45}\n")
    )
    result = load_specs(tmp_path)
    assert [spec.id for spec in result.specs] == ["good"]
    assert len(result.errors) == 2


def test_duplicate_id_keeps_first_by_filename(tmp_path: Path):
    item = "  - id: same\n    photo: {width_mm: 35, height_mm: 45}\n"
    (tmp_path / "a.yaml").write_text(_document(item, "FIRST"))
    (tmp_path / "b.yaml").write_text(_document(item, "SECOND"))
    result = load_specs(tmp_path)
    assert result.specs[0].country_id == "FIRST"
    assert "duplicate id" in result.errors[0]


def test_invalid_optional_format_does_not_hide_valid_sibling(tmp_path: Path):
    (tmp_path / "mixed.yaml").write_text(
        _document(
            "  - id: bad\n"
            "    photo: {width_mm: 35, height_mm: 45}\n"
            "    face: {min_head_height_ratio: 0.8, max_head_height_ratio: 0.7}\n"
            "  - id: good\n"
            "    photo: {width_mm: 35, height_mm: 45}\n"
            "    future_field: {allowed: true}\n"
        )
    )
    result = load_specs(tmp_path)
    assert [spec.id for spec in result.specs] == ["good"]
    assert len(result.errors) == 1


def test_known_optional_types_and_head_region_bounds_are_validated(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text(
        _document(
            "  - id: bad\n"
            "    photo: {width_mm: 35, height_mm: 45}\n"
            "    guides:\n"
            "      center_line: yes\n"
            "      head_region: {enabled: true, x: 0.8, y: 0.1, width: 0.3, height: 0.5}\n"
            "    source: {url: [not-a-string]}\n"
        )
    )
    result = load_specs(tmp_path)
    assert result.specs == []
    assert result.errors


def test_nullable_schema_and_boolean_background(tmp_path):
    (tmp_path / "optional.yaml").write_text(_document(
        "  - id: optional\n"
        "    photo: {width_mm: 35, height_mm: 45}\n"
        "    face: {center_face: null}\n"
        "    background: {preferred: white, required: true}\n"
        "    guides:\n"
        "      center_line: null\n"
        "      head_region: {enabled: true, x: null, y: null, width: null, height: null}\n"
    ))
    result = load_specs(tmp_path)
    assert not result.errors
    assert result.specs[0].background["required"] is True


def test_builtin_configs_and_generic_guides():
    from photoscpec.core.guides import get_guides
    root = Path(__file__).resolve().parents[2]
    result = load_specs(root / "configs")
    assert not result.errors
    assert len(result.specs) >= 6
    assert get_guides(None).guides
