from pathlib import Path

from photoscpec.config import load_specs


def test_loads_multiple_countries_and_yaml_extensions(tmp_path: Path):
    (tmp_path / "a.yaml").write_text(
        "id: a\nname: A\ncategory: passport\ncountry_id: AA\n"
        "country_name: Alpha\nwidth_mm: 35\nheight_mm: 45\ndefault_dpi: 300\n"
    )
    (tmp_path / "b.yml").write_text(
        "id: b\nname: B\ncategory: visa\ncountry_id: BB\n"
        "country_name: Beta\nwidth_mm: 50.8\nheight_mm: 50.8\ndefault_dpi: 300\n"
    )
    result = load_specs(tmp_path)
    assert [spec.id for spec in result.specs] == ["a", "b"]
    assert result.errors == []


def test_malformed_file_does_not_hide_valid_file(tmp_path: Path):
    (tmp_path / "bad.yaml").write_text("specifications: [")
    (tmp_path / "good.yaml").write_text(
        "id: good\nname: Good\ncategory: passport\ncountry_id: AA\n"
        "country_name: Alpha\nwidth_mm: 35\nheight_mm: 45\ndefault_dpi: 300\n"
    )
    result = load_specs(tmp_path)
    assert [spec.id for spec in result.specs] == ["good"]
    assert len(result.errors) == 1


def test_duplicate_id_is_deterministic_and_keeps_first(tmp_path: Path):
    base = (
        "id: same\ncategory: passport\ncountry_id: AA\ncountry_name: Alpha\n"
        "width_mm: 35\nheight_mm: 45\ndefault_dpi: 300\n"
    )
    (tmp_path / "a.yaml").write_text("name: First\n" + base)
    (tmp_path / "b.yaml").write_text("name: Second\n" + base)
    result = load_specs(tmp_path)
    assert [spec.name for spec in result.specs] == ["First"]
    assert "duplicate id" in result.errors[0]


def test_invalid_optional_metadata_rejects_only_that_entry(tmp_path: Path):
    (tmp_path / "mixed.yaml").write_text(
        "specifications:\n"
        "  - {id: bad, name: Bad, category: passport, country_id: AA, "
        "country_name: Alpha, width_mm: 35, height_mm: 45, default_dpi: 300, "
        "face: {head_height_min_ratio: 0.8, head_height_max_ratio: 0.7}}\n"
        "  - {id: good, name: Good, category: passport, country_id: AA, "
        "country_name: Alpha, width_mm: 35, height_mm: 45, default_dpi: 300}\n"
    )
    result = load_specs(tmp_path)
    assert [spec.id for spec in result.specs] == ["good"]
    assert len(result.errors) == 1
