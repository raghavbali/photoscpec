# Headless core

## Context
Streamlit is convenient for a local UI but should be replaceable.

## Decision
Use explicit dataclasses and one stateless service facade over focused core modules.

## Alternatives considered
All-in-one Streamlit app; HTTP-first microservice.

## Consequences
Backend tests require no UI process; future adapters reuse the engine; no unnecessary server.
