"""Exact-copy print layout calculation."""
import math

from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import LayoutRequest, LayoutResult, PhotoPlacement


def _finite_nonnegative(value: float, name: str, positive: bool = False) -> None:
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise PhotoScpecError("INVALID_DIMENSIONS", f"{name} is invalid", {"field": name})


def _capacity(pw, ph, fw, fh, margin, spacing):
    usable_w, usable_h = pw - 2 * margin, ph - 2 * margin
    if usable_w < fw or usable_h < fh:
        return 0, 0, 0
    columns = int(math.floor((usable_w + spacing + 1e-9) / (fw + spacing)))
    rows = int(math.floor((usable_h + spacing + 1e-9) / (fh + spacing)))
    return rows * columns, rows, columns


def calculate_layout(request: LayoutRequest) -> LayoutResult:
    for value, name, positive in (
        (request.photo_width_mm, "photo_width_mm", True),
        (request.photo_height_mm, "photo_height_mm", True),
        (request.paper_width_mm, "paper_width_mm", True),
        (request.paper_height_mm, "paper_height_mm", True),
        (request.spacing_mm, "spacing_mm", False),
        (request.margin_mm, "margin_mm", False),
    ):
        _finite_nonnegative(value, name, positive)
    if isinstance(request.copies, bool) or not isinstance(request.copies, int) or request.copies <= 0:
        raise PhotoScpecError("INVALID_DIMENSIONS", "copies must be a positive integer")
    if request.copies > 10_000:
        raise PhotoScpecError("INVALID_DIMENSIONS", "copies exceed the layout limit")
    if request.layout_mode not in {"auto", "grid"}:
        raise PhotoScpecError("INVALID_DIMENSIONS", "layout_mode must be auto or grid")
    if request.orientation not in {None, "portrait", "landscape"}:
        raise PhotoScpecError("INVALID_DIMENSIONS",
                              "orientation must be portrait or landscape")

    if request.orientation == "portrait":
        papers = [("portrait", min(request.paper_width_mm, request.paper_height_mm),
                   max(request.paper_width_mm, request.paper_height_mm))]
    elif request.orientation == "landscape":
        papers = [("landscape", max(request.paper_width_mm, request.paper_height_mm),
                   min(request.paper_width_mm, request.paper_height_mm))]
    else:
        papers = [
            ("portrait", min(request.paper_width_mm, request.paper_height_mm),
             max(request.paper_width_mm, request.paper_height_mm)),
            ("landscape", max(request.paper_width_mm, request.paper_height_mm),
             min(request.paper_width_mm, request.paper_height_mm)),
        ]

    candidates = []
    rotations = [False, True] if request.allow_rotate else [False]
    for orientation, pw, ph in papers:
        for rotated in rotations:
            fw, fh = ((request.photo_height_mm, request.photo_width_mm) if rotated else
                      (request.photo_width_mm, request.photo_height_mm))
            capacity, rows, columns = _capacity(
                pw, ph, fw, fh, request.margin_mm, request.spacing_mm)
            if request.layout_mode == "grid":
                if (not isinstance(request.rows, int) or isinstance(request.rows, bool)
                        or not isinstance(request.columns, int)
                        or isinstance(request.columns, bool)
                        or request.rows <= 0 or request.columns <= 0):
                    raise PhotoScpecError("INVALID_DIMENSIONS",
                                          "Grid rows and columns must be positive")
                rows, columns = request.rows, request.columns
                need_w = columns * fw + (columns - 1) * request.spacing_mm
                need_h = rows * fh + (rows - 1) * request.spacing_mm
                capacity = rows * columns if (
                    need_w <= pw - 2 * request.margin_mm + 1e-9
                    and need_h <= ph - 2 * request.margin_mm + 1e-9) else 0
            candidates.append((capacity, rows, columns, orientation, pw, ph, rotated, fw, fh))

    viable = [candidate for candidate in candidates if candidate[0] >= request.copies]
    maximum = max((candidate[0] for candidate in candidates), default=0)
    if not viable:
        raise PhotoScpecError("LAYOUT_DOES_NOT_FIT",
                              "Requested copies do not fit without shrinking",
                              {"requested": request.copies, "maximum_capacity": maximum})
    chosen = min(viable, key=lambda candidate: (
        -candidate[0], candidate[6], candidate[3] == "landscape"))
    capacity, rows, columns, orientation, pw, ph, rotated, fw, fh = chosen
    grid_w = columns * fw + (columns - 1) * request.spacing_mm
    grid_h = rows * fh + (rows - 1) * request.spacing_mm
    origin_x, origin_y = (pw - grid_w) / 2, (ph - grid_h) / 2
    positions = []
    for index in range(request.copies):
        row, column = divmod(index, columns)
        positions.append(PhotoPlacement(
            origin_x + column * (fw + request.spacing_mm),
            origin_y + row * (fh + request.spacing_mm), fw, fh, rotated))
    return LayoutResult(rows, columns, capacity, len(positions), orientation, pw, ph, positions)
