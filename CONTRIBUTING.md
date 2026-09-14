# Contributing

PhotoScpec is a small personal-use app. Keep changes focused and avoid new services or dependencies unless they solve an actual problem.

Start meaningful work with a GitHub issue and an implementation-plan comment describing approach, files, decisions, acceptance criteria and tests. Use a feature branch and small commits; update progress for meaningful milestones. Open a PR with what/why, how to test, results, examples and known limitations. Review code, physical geometry, tests, configuration and architecture before merge. CI must pass. Use a final issue comment with result, tests, limitations and PR link before closing.

## Document-format template

```text
Country:
Document:
Category:
Photo width:
Photo height:
Official source:
Source URL:
Last verified:
Face/head requirements:
Notes:
```

Add YAML under configs, usually without Python changes. Do not claim acceptance guarantees or infer digital requirements from paper dimensions.

```bash
uv sync
uv run ruff check .
uv run python scripts/validate_configs.py
uv run pytest -q
```

Backend code must not import Streamlit/frontend. Crop coordinates are normalized after EXIF orientation and rotation. Never fill unused grid slots, silently reduce physical dimensions, or burn positioning guides into exports. Include regression coverage for affected behavior and update public interface docs when contracts change.
