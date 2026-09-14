# Frontend/backend contract

## Context
A future HTTP or desktop adapter needs stable transport-friendly behavior.

## Decision
Public requests/responses use dataclasses, primitives and bytes. Services never see UI state. Guides are geometry data, not drawings.

## Alternatives considered
PIL objects in public models; arbitrary widget dictionaries; premature REST server.

## Consequences
Small in-process MVP with clear future multipart/JSON mapping. Backend raises structured errors; frontend draws preview-only guides.
