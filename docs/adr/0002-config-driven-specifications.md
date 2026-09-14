# Configuration-driven specifications

## Context
Document requirements differ by use and can change independently of the engine.

## Decision
Load country/formats YAML dynamically, validate fields, isolate bad entries and retain provenance.

## Alternatives considered
UI constants; database-backed format editor.

## Consequences
New formats normally need YAML only; user still verifies official rules; no acceptance guarantees.
