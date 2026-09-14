"""Typed photo specification model."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PhotoSpec:
    id: str
    name: str
    category: str
    country_id: str
    country_name: str
    width_mm: float
    height_mm: float
    default_dpi: int
    face: dict = field(default_factory=dict)
    background: dict = field(default_factory=dict)
    guides: dict = field(default_factory=dict)
    printing: dict = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    source: dict = field(default_factory=dict)
