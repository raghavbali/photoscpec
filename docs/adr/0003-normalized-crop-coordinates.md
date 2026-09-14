# Normalized crop coordinates

## Context
Preview dimensions vary across browser windows and frontends.

## Decision
Use 0–1 crop rectangles after EXIF orientation and clockwise quarter-turn rotation. Convert only inside the crop engine.

## Alternatives considered
Preview-pixel coordinates; persisted full-resolution pixel rectangles.

## Consequences
Cropping is independent of preview size; callers must use the documented coordinate frame; ratio validation prevents stretching.
