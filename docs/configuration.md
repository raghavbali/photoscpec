# Add photo specifications

Create configs/<country>.yaml (or .yml), then restart the app. No Python changes are needed. Category is descriptive free text.

```yaml
country:
  id: example
  name: Example
formats:
  - id: example_document
    name: Example document
    category: application_form
    photo:
      width_mm: 35
      height_mm: 45
      default_dpi: 300
    face:
      min_head_height_ratio: null
      max_head_height_ratio: null
      eye_line_ratio: null
      center_face: true
    background:
      preferred: white
      required: null
    guides:
      center_line: true
      eye_line:
        enabled: true
        position_ratio: 0.45
      crown_line:
        enabled: true
      chin_line:
        enabled: true
      head_region:
        enabled: true
        x: 0.25
        y: 0.10
        width: 0.50
        height: 0.75
    printing:
      preferred_spacing_mm: 2
    notes:
      - A template only. Verify official requirements.
    source:
      authority: null
      url: null
      last_verified: null
```

Country/format IDs and positive physical dimensions are essential. Descriptive metadata, DPI (default 300), optional face/background rules and guides have defaults. Guide ratios use 0–1 with origin at the top-left: eye position 0.45 means 45% down from the top. Guide bounds must stay within the photo. Enabled crown/chin defaults are positioning aids, not official measurements.

Source metadata describes provenance; never enter a verification date without checking the requirement. Quote a date as a YAML string, e.g. "2026-09-14". A null date means unverified. This app does not fetch source URLs or enforce optional facial/background metadata.

Files load in filename order. Duplicate IDs keep the first valid definition and report a diagnostic. Malformed files and invalid entries are reported without discarding unrelated valid formats. Review startup warnings after adding community configs.

```bash
uv run python scripts/validate_configs.py
uv run pytest -q
```

The validation command exits nonzero if it finds errors. Built-ins are validated in CI.
