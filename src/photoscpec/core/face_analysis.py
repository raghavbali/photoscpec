"""Optional face-analysis seam; the default implementation performs no ML."""
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class FaceAnalysis:
    detected: bool
    faces: int = 0
    confidence: float | None = None
    landmarks: dict = field(default_factory=dict)


class FaceAnalyzer(Protocol):
    def analyze(self, image: bytes) -> FaceAnalysis:
        """Analyze encoded image bytes without changing them."""


class NoOpFaceAnalyzer:
    def analyze(self, image: bytes) -> FaceAnalysis:
        return FaceAnalysis(detected=False)
