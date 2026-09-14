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


_REQUIRED_STRINGS = ("id", "name", "category", "country_id", "country_name")
_DICT_FIELDS = ("face", "background", "guides", "printing", "source")
_RATIO_KEYS = {
    "eye_line_ratio",
    "chin_line_ratio",
    "crown_line_ratio",
    "face_center_x",
    "face_center_y",
}
_BOUNDS_KEYS = ("face_bounds", "safe_area")


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        qualifier = "a finite positive number" if positive else "finite"
        raise ValueError(f"{label} must be {qualifier}")
    return result


def _validate_metadata(data: dict[str, Any]) -> None:
    for field_name in _DICT_FIELDS:
        value = data.get(field_name, {})
        if value is not None and not isinstance(value, dict):
            raise ValueError(f"{field_name} must be a mapping")
    notes = data.get("notes", [])
    if notes is not None and (
        not isinstance(notes, list) or not all(isinstance(note, str) for note in notes)
    ):
        raise ValueError("notes must be a list of strings")

    guides = data.get("guides") or {}
    for key in _RATIO_KEYS:
        if key in guides:
            ratio = _number(guides[key], f"guides.{key}")
            if not 0 <= ratio <= 1:
                raise ValueError(f"guides.{key} must be between 0 and 1")
    for key in _BOUNDS_KEYS:
        if key not in guides:
            continue
        bounds = guides[key]
        if not isinstance(bounds, dict):
            raise ValueError(f"guides.{key} must be a mapping")
        for component in ("x", "y", "width", "height"):
            value = _number(bounds.get(component), f"guides.{key}.{component}")
            if not 0 <= value <= 1:
                raise ValueError(f"guides.{key}.{component} must be between 0 and 1")
        if bounds["x"] + bounds["width"] > 1 or bounds["y"] + bounds["height"] > 1:
            raise ValueError(f"guides.{key} must fit inside the normalized image")

    face = data.get("face") or {}
    for key in ("head_height_min_ratio", "head_height_max_ratio"):
        if key in face:
            value = _number(face[key], f"face.{key}")
            if not 0 <= value <= 1:
                raise ValueError(f"face.{key} must be between 0 and 1")
    minimum = face.get("head_height_min_ratio")
    maximum = face.get("head_height_max_ratio")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("face head height minimum cannot exceed maximum")

    source = data.get("source") or {}
    if "urls" in source and (
        not isinstance(source["urls"], list)
        or not all(isinstance(url, str) for url in source["urls"])
    ):
        raise ValueError("source.urls must be a list of strings")
    if "last_verified" in source and source["last_verified"] is not None and not isinstance(
        source["last_verified"], str
    ):
        raise ValueError("source.last_verified must be a string or null")


def _parse_spec(data: Any) -> PhotoSpec:
    if not isinstance(data, dict):
        raise ValueError("specification must be a mapping")
    for key in _REQUIRED_STRINGS:
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    width = _number(data.get("width_mm"), "width_mm", positive=True)
    height = _number(data.get("height_mm"), "height_mm", positive=True)
    dpi = data.get("default_dpi")
    if isinstance(dpi, bool) or not isinstance(dpi, int) or dpi <= 0:
        raise ValueError("default_dpi must be a positive integer")
    _validate_metadata(data)
    return PhotoSpec(
        id=data["id"].strip(),
        name=data["name"].strip(),
        category=data["category"].strip(),
        country_id=data["country_id"].strip(),
        country_name=data["country_name"].strip(),
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


def _documents(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and "specifications" in payload:
        items = payload["specifications"]
        if not isinstance(items, list):
            raise ValueError("specifications must be a list")
        return items
    return [payload]


def load_specs(config_dir: str | Path) -> ConfigLoadResult:
    """Load every YAML file, retaining valid entries when others fail."""
    root = Path(config_dir)
    errors: list[str] = []
    specs_by_id: dict[str, PhotoSpec] = {}
    paths = sorted((*root.glob("*.yaml"), *root.glob("*.yml")), key=lambda item: item.name)
    if not root.is_dir():
        return ConfigLoadResult([], [f"{root}: configuration directory does not exist"])
    for path in paths:
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            documents = _documents(payload)
        except (OSError, yaml.YAMLError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        for index, document in enumerate(documents, start=1):
            label = f"{path.name} entry {index}"
            try:
                spec = _parse_spec(document)
            except (TypeError, ValueError) as exc:
                errors.append(f"{label}: {exc}")
                continue
            if spec.id in specs_by_id:
                errors.append(
                    f"{label}: duplicate id {spec.id!r}; keeping first definition"
                )
                continue
            specs_by_id[spec.id] = spec
    return ConfigLoadResult(list(specs_by_id.values()), errors)
