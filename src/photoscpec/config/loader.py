"""Resilient YAML loading and validation for photo specifications."""
from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import yaml

from .models import PhotoSpec


@dataclass(frozen=True)
class ConfigLoadResult:
    specs: list[PhotoSpec]
    errors: list[str]


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        qualifier = "a finite positive number" if positive else "finite"
        raise ValueError(f"{label} must be {qualifier}")
    return result


def _optional_ratio(value: Any, label: str) -> None:
    if value is None:
        return
    ratio = _number(value, label)
    if not 0 <= ratio <= 1:
        raise ValueError(f"{label} must be between 0 and 1 or null")


def _mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping")
    return value


def _validate_optional(data: dict[str, Any]) -> None:
    face = _mapping(data, "face")
    for key in ("min_head_height_ratio", "max_head_height_ratio", "eye_line_ratio"):
        if key in face:
            _optional_ratio(face[key], f"face.{key}")
    if "center_face" in face and not isinstance(face["center_face"], bool):
        raise ValueError("face.center_face must be a boolean")
    minimum = face.get("min_head_height_ratio")
    maximum = face.get("max_head_height_ratio")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("face minimum head height cannot exceed maximum")

    background = _mapping(data, "background")
    for key in ("preferred", "required"):
        if key in background and background[key] is not None and not isinstance(
            background[key], str
        ):
            raise ValueError(f"background.{key} must be a string or null")

    guides = _mapping(data, "guides")
    if "center_line" in guides and not isinstance(guides["center_line"], bool):
        raise ValueError("guides.center_line must be a boolean")
    eye = _mapping(guides, "eye_line")
    for key in ("crown_line", "chin_line"):
        item = _mapping(guides, key)
        if "enabled" in item and not isinstance(item["enabled"], bool):
            raise ValueError(f"guides.{key}.enabled must be a boolean")
    if "enabled" in eye and not isinstance(eye["enabled"], bool):
        raise ValueError("guides.eye_line.enabled must be a boolean")
    if "position_ratio" in eye:
        _optional_ratio(eye["position_ratio"], "guides.eye_line.position_ratio")

    region = _mapping(guides, "head_region")
    if "enabled" in region and not isinstance(region["enabled"], bool):
        raise ValueError("guides.head_region.enabled must be a boolean")
    coordinates = []
    for key in ("x", "y", "width", "height"):
        if key not in region:
            continue
        value = _number(region[key], f"guides.head_region.{key}")
        if not 0 <= value <= 1:
            raise ValueError(f"guides.head_region.{key} must be between 0 and 1")
        if key in ("width", "height") and value <= 0:
            raise ValueError(f"guides.head_region.{key} must be positive")
        coordinates.append(key)
    if coordinates and len(coordinates) != 4:
        raise ValueError("guides.head_region requires x, y, width, and height")
    if coordinates and (
        region["x"] + region["width"] > 1 or region["y"] + region["height"] > 1
    ):
        raise ValueError("guides.head_region must fit inside the normalized image")

    printing = _mapping(data, "printing")
    if "preferred_spacing_mm" in printing and printing["preferred_spacing_mm"] is not None:
        spacing = _number(printing["preferred_spacing_mm"], "printing.preferred_spacing_mm")
        if spacing < 0:
            raise ValueError("printing.preferred_spacing_mm cannot be negative")

    source = _mapping(data, "source")
    for key in ("authority", "url", "last_verified"):
        if key in source and source[key] is not None and not isinstance(source[key], str):
            raise ValueError(f"source.{key} must be a string or null")

    notes = data.get("notes")
    if notes is not None and (
        not isinstance(notes, list) or not all(isinstance(note, str) for note in notes)
    ):
        raise ValueError("notes must be a list of strings")


def _parse_format(country: dict[str, str], data: Any) -> PhotoSpec:
    if not isinstance(data, dict):
        raise ValueError("format must be a mapping")
    identifier = data.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError("format id must be a non-empty string")
    photo = data.get("photo")
    if not isinstance(photo, dict):
        raise ValueError("photo must be a mapping")
    width = _number(photo.get("width_mm"), "photo.width_mm", positive=True)
    height = _number(photo.get("height_mm"), "photo.height_mm", positive=True)
    dpi = photo.get("default_dpi", 300)
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0:
        raise ValueError("photo.default_dpi must be a positive integer")
    for key in ("name", "category"):
        if key in data and (not isinstance(data[key], str) or not data[key].strip()):
            raise ValueError(f"{key} must be a non-empty string")
    _validate_optional(data)
    return PhotoSpec(
        id=identifier.strip(),
        name=data.get("name", identifier).strip(),
        category=data.get("category", "custom").strip(),
        country_id=country["id"],
        country_name=country["name"],
        width_mm=width,
        height_mm=height,
        default_dpi=dpi,
        face=dict(data.get("face") or {}),
        background=dict(data.get("background") or {}),
        guides=dict(data.get("guides") or {}),
        printing=dict(data.get("printing") or {}),
        notes=list(data.get("notes") or []),
        source=dict(data.get("source") or {}),
    )


def _parse_file(payload: Any) -> list[PhotoSpec]:
    if not isinstance(payload, dict):
        raise ValueError("document must be a mapping")
    raw_country = payload.get("country")
    if not isinstance(raw_country, dict):
        raise ValueError("country must be a mapping")
    country_id = raw_country.get("id")
    if not isinstance(country_id, str) or not country_id.strip():
        raise ValueError("country.id must be a non-empty string")
    country_name = raw_country.get("name", country_id)
    if not isinstance(country_name, str) or not country_name.strip():
        raise ValueError("country.name must be a non-empty string")
    formats = payload.get("formats")
    if not isinstance(formats, list):
        raise ValueError("formats must be a list")
    country = {"id": country_id.strip(), "name": country_name.strip()}
    specs = []
    for index, item in enumerate(formats, start=1):
        try:
            specs.append(_parse_format(country, item))
        except (TypeError, ValueError) as exc:
            specs.append(exc)
    return specs


def load_specs(config_dir: str | Path) -> ConfigLoadResult:
    """Load all YAML files, retaining valid formats when other inputs fail."""
    root = Path(config_dir)
    if not root.is_dir():
        return ConfigLoadResult([], [f"{root}: configuration directory does not exist"])
    errors: list[str] = []
    specs_by_id: dict[str, PhotoSpec] = {}
    paths = sorted((*root.glob("*.yaml"), *root.glob("*.yml")), key=lambda path: path.name)
    for path in paths:
        try:
            parsed = _parse_file(yaml.safe_load(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        for index, item in enumerate(parsed, start=1):
            label = f"{path.name} format {index}"
            if isinstance(item, Exception):
                errors.append(f"{label}: {item}")
                continue
            if item.id in specs_by_id:
                errors.append(f"{label}: duplicate id {item.id!r}; keeping first definition")
                continue
            specs_by_id[item.id] = item
    return ConfigLoadResult(list(specs_by_id.values()), errors)
