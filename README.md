# PhotoScpec

Prepare correctly sized document photos locally.

PhotoScpec is a privacy-first local tool for preparing passport, visa, identity and document photos for printing. Its Python engine works independently of the Streamlit frontend.

## Install and run

Requires Python 3.12+; uv can install Python for you. From a terminal on macOS (Apple Silicon supported), Linux or Windows:

```bash
git clone https://github.com/raghavbali/photoscpec.git
cd photoscpec
# Install uv if needed (macOS/Linux):
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
uv run streamlit run frontend/streamlit/app.py
```

Open the localhost address printed in the terminal. Run from the repository root so Streamlit reads the local-only server and disabled-telemetry settings. Stop with Ctrl+C. Dependencies download during installation; normal photo preparation works offline afterward. On Windows install uv using its Windows installer.

## Use

1. Select a country/document preset or Custom. Custom accepts mm, inch or px. Choose DPI and optionally lock width/height ratio.
2. Upload JPG/JPEG/PNG. Use zoom, horizontal/vertical pan and clockwise quarter turns to frame the face. Preview positioning guides if useful.
3. Download the cropped individual PNG/JPG at the displayed pixel dimensions.
4. Choose copies, paper, grid, spacing and margins. Preview the sheet and download PDF, PNG or JPG.
5. Print at **Actual Size / 100%** on the selected paper, with **Fit to Page disabled**.

Physical photo size, digital pixel resolution, and paper size are separate. For an exact **630 × 810 px** digital upload, choose Custom → px → 630 × 810. At 300 DPI this implies 53.34 × 68.58 mm for printing; it does not imply a 35 × 45 mm physical photo.

The initial catalog includes India passport/OCI-style 51 × 51 mm, India birth/consular 35 × 45 mm, US passport/visa 50.8 × 50.8 mm (2 inches), UK passport 35 × 45 mm and generic EU/Schengen 35 × 45 mm.

**Requirements may change. Verify the latest official requirements before submission.** These are preparation templates, not acceptance guarantees. Digital and paper requirements can differ. Positioning guides are visual aids only. They do not certify biometric or government compliance.

## Privacy

Images are processed in memory on your own machine. There are no cloud image services, accounts, analytics or image files written by the application. Streamlit runs on 127.0.0.1 with usage reporting disabled. Do not expose the server publicly: this personal-use app has no authentication. Uploaded bytes and prepared downloads exist temporarily in the running session; clearing the upload/resetting the session or stopping the app releases application references. Your browser/OS can retain memory or downloaded files. Exports remove source EXIF metadata and composite transparency on white; the original file is untouched.

## Printing and limits

The engine never reduces physical photo dimensions to fit a sheet and produces exactly the requested number of copies. Auto fit evaluates portrait/landscape paper and uniform photo rotation; it does not attempt mixed-orientation packing. A grid describes rows × columns, not required copies. Eight 35 × 45 mm photos do **not** fit a 4 × 6 inch sheet with 3 mm margins and 2 mm spacing: the uniform-grid maximum is six. Choose a larger sheet or fewer copies.

PDF uses exact millimeter geometry. Raster sheets round to the nearest pixel, so physical accuracy is limited to roughly one pixel plus printer tolerances. Low-resolution sources can be upscaled with a warning; this does not add detail. HEIC, background replacement and automatic facial/compliance analysis are outside the MVP.

## Development

```bash
uv run ruff check .
uv run python scripts/validate_configs.py
uv run pytest -q
```

CI runs the same checks on Linux and macOS with Python 3.12. uv creates an isolated .venv and a resolved uv.lock; retain the lock when installing locally. Dependency version ranges live in pyproject.toml.

Backend code is in src/photoscpec; only frontend/streamlit imports Streamlit. YAML specifications load dynamically from configs. No HTTP server or database is required.

- [Architecture](docs/architecture.md)
- [Public interfaces](docs/interfaces.md)
- [Add specifications](docs/configuration.md)
- [Printing](docs/printing.md)
- [Contribute](CONTRIBUTING.md)
- [Future HTTP adapter](adapters/http/README.md)
