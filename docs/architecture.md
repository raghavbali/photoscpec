# Architecture

The dependency direction is frontend → services/public contracts → core + configuration → Pillow/PyYAML/ReportLab. Backend modules never import Streamlit or UI state; an AST-based test enforces this.

PhotoScpecService provides one small facade. Stateless operations take explicit dataclasses and image bytes; the service retains only a specification catalog and loading diagnostics. There is no image-ID store, database, background process, authentication, HTTP server or ML model.

- interfaces/models.py: plain dataclasses for dimensions, normalized crop, guide geometry, print layout and export.
- interfaces/errors.py: structured exception with code, message and primitive details.
- config: validates YAML, preserves valid entries and reports invalid files/entries.
- core: conversions, bounded decoding, crop, guide data, physical layout and export.
- services: application-facing facade.
- frontend/streamlit: controls, ephemeral state, request mapping and preview-only guide drawing.

Paper presets are presentation choices; document presets belong exclusively in YAML. Cropping and layout are engine operations. The frontend can use Pillow to draw guide overlays on a preview copy; export receives clean crop bytes.

Operations retain no image state. New HTTP/native frontends can call the same facade. For a packaged wheel outside this checkout, supply an explicit config_dir to the service; the supported MVP deployment is the documented git checkout with uv sync.

The intentionally compact implementation uses one facade and consolidated request/response dataclasses rather than separate services that only forward calls. See the four ADRs for decisions and tradeoffs.
