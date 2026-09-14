from __future__ import annotations

import streamlit as st

from frontend.streamlit.ui_helpers import (
    GRID_SHAPES, PAPERS_MM, crop_frame_request, guide_preview, keep_ratio_from_height,
    keep_ratio_from_width, layout_request, photo_export_key, sheet_export_key,
)
from photoscpec.interfaces.errors import PhotoScpecError
from photoscpec.interfaces.models import (
    CropRequest, DimensionsRequest, GuideRequest, PhotoExportRequest, SheetExportRequest,
    ValidationRequest,
)
from photoscpec.services.photoscpec_service import PhotoScpecService

DISCLAIMER = "Requirements may change. Verify the latest official requirements before submission."
GUIDE_NOTICE = ("Positioning guides are visual aids only. They do not certify biometric or "
                "government compliance.")


def show_error(error: PhotoScpecError) -> None:
    st.error(str(error))
    if error.code == "LAYOUT_DOES_NOT_FIT":
        st.info("Choose fewer copies, reduce spacing or margins, or select larger paper.")
    if error.details:
        st.caption(" · ".join(f"{key}: {value}" for key, value in error.details.items()))


def note_text(notes) -> str:
    if isinstance(notes, (list, tuple)):
        return "\n".join(f"• {note}" for note in notes)
    return str(notes)


def printing_default(printing, key: str, fallback: float) -> float:
    if isinstance(printing, dict):
        value = printing.get(key)
        return float(value) if value is not None else fallback
    return fallback


def dimensions_panel(service, specs):
    st.subheader("1. Photo size")
    countries = sorted({(s.country_id, s.country_name) for s in specs}, key=lambda pair: pair[1])
    selected_country = st.selectbox("Country", ["Custom"] + [name for _, name in countries],
                                    index=1 if countries else 0)
    spec = None
    if selected_country != "Custom":
        country_id = next(identifier for identifier, name in countries if name == selected_country)
        labels = {f"{s.name} — {s.category}": s for s in specs if s.country_id == country_id}
        spec = labels[st.selectbox("Document", list(labels))]
        if st.session_state.get("_defaults_spec_id") != spec.id:
            st.session_state.dpi = spec.default_dpi
            st.session_state.spacing_mm = printing_default(spec.printing, "preferred_spacing_mm", 2.0)
            st.session_state._defaults_spec_id = spec.id
        choices = sorted({150, 200, 300, 600, int(spec.default_dpi)})
        dpi = st.selectbox("DPI", choices, key="dpi")
        request = DimensionsRequest(spec.width_mm, spec.height_mm, "mm", dpi)
        if spec.notes:
            st.info(note_text(spec.notes))
    else:
        unit = st.selectbox("Unit", ["mm", "inch", "px"])
        if st.session_state.get("_custom_unit") != unit:
            neutral = 100.0 if unit == "px" else 1.0
            st.session_state.custom_width = neutral
            st.session_state.custom_height = neutral
            st.session_state.custom_ratio = 1.0
            st.session_state._custom_unit = unit
        st.checkbox("Maintain aspect ratio", key="maintain_ratio")
        left, right = st.columns(2)
        callback_width = keep_ratio_from_width if st.session_state.maintain_ratio else None
        callback_height = keep_ratio_from_height if st.session_state.maintain_ratio else None
        step = 1.0 if unit == "px" else 0.1
        with left:
            st.number_input("Width", min_value=None, step=step, key="custom_width",
                            on_change=callback_width, args=(st.session_state,))
        with right:
            st.number_input("Height", min_value=None, step=step, key="custom_height",
                            on_change=callback_height, args=(st.session_state,))
        if not st.session_state.maintain_ratio and st.session_state.custom_height:
            st.session_state.custom_ratio = (
                st.session_state.custom_width / st.session_state.custom_height)
        dpi = st.selectbox("DPI", [150, 200, 300, 600], index=2, key="custom_dpi")
        request = DimensionsRequest(float(st.session_state.custom_width),
                                    float(st.session_state.custom_height), unit, dpi)
    st.caption(DISCLAIMER)
    dimensions = service.resolve_dimensions(request)
    st.write(f"Target: **{dimensions.width_mm:g} × {dimensions.height_mm:g} mm** · "
             f"**{dimensions.width_px} × {dimensions.height_px} px** at {dimensions.dpi} DPI")
    return spec, dimensions


def export_photo_controls(service, cropped, dpi):
    st.subheader("4. Download photo")
    image_format = st.radio("Individual format", ["JPG", "PNG"], horizontal=True)
    current_key = photo_export_key(cropped.image, dpi, image_format)
    if st.button(f"Prepare {image_format} photo"):
        result = service.export_photo(PhotoExportRequest(cropped.image, image_format, dpi))
        st.session_state.photo_export = (current_key, result)
    saved = st.session_state.get("photo_export")
    if saved is not None and saved[0] == current_key:
        result = saved[1]
        st.download_button("Download individual photo", result.data, result.filename,
                           result.mime_type)


def print_panel(service, cropped, dimensions, printing):
    st.subheader("5. Print sheet")
    copies = st.number_input("Copies", 1, 100, 4)
    paper_name = st.selectbox("Paper", [*PAPERS_MM, "Custom"])
    if paper_name == "Custom":
        a, b = st.columns(2)
        paper = (a.number_input("Paper width (mm)", 1.0, value=210.0),
                 b.number_input("Paper height (mm)", 1.0, value=297.0))
    else:
        paper = PAPERS_MM[paper_name]
    grid = st.selectbox("Grid", ["Auto", *GRID_SHAPES, "Custom"])
    rows = columns = None
    if grid == "Custom":
        a, b = st.columns(2)
        rows = a.number_input("Rows", 1, 50, 2)
        columns = b.number_input("Columns", 1, 50, 2)
    default_spacing = printing_default(printing, "preferred_spacing_mm", 2.0)
    st.session_state.setdefault("spacing_mm", default_spacing)
    spacing = st.number_input("Spacing (mm)", 0.0, key="spacing_mm")
    margin = st.number_input("Margins (mm)", 0.0, value=3.0)
    cut_guides = st.checkbox("Cutting guides", value=True)
    orientation_label = st.selectbox("Paper orientation", ["Auto", "Portrait", "Landscape"])
    orientation = None if orientation_label == "Auto" else orientation_label.lower()
    request = layout_request(dimensions.width_mm, dimensions.height_mm, paper, int(copies),
                             spacing, margin, grid, rows, columns, orientation)
    try:
        layout = service.calculate_layout(request)
        st.caption(f"Page: {layout.paper_width_mm:g} × {layout.paper_height_mm:g} mm · "
                   f"Capacity: {layout.capacity} · Spacing: {spacing:g} mm · "
                   f"Margins: {margin:g} mm")
        st.write(f"{layout.rows} rows × {layout.columns} columns · "
                 f"{layout.copies_rendered}/{copies} copies · {layout.orientation}")
        for warning in layout.warnings:
            st.warning(warning)
        preview = service.export_sheet(
            SheetExportRequest(cropped.image, request, "PNG", 100, cut_guides))
        st.image(preview.data, caption="Print sheet preview")
        image_format = st.radio("Sheet format", ["PDF", "JPG", "PNG"], horizontal=True)
        current_key = sheet_export_key(cropped.image, request, dimensions.dpi,
                                       image_format, cut_guides)
        if st.button(f"Prepare {image_format} sheet"):
            result = service.export_sheet(SheetExportRequest(
                cropped.image, request, image_format, dimensions.dpi, cut_guides))
            st.session_state.sheet_export = (current_key, result)
        saved = st.session_state.get("sheet_export")
        if saved is not None and saved[0] == current_key:
            result = saved[1]
            st.download_button("Download print sheet", result.data, result.filename,
                               result.mime_type)
    except PhotoScpecError as error:
        show_error(error)
    st.info("Print at Actual Size / 100%. Disable Fit to Page and use the same paper size.")


def main() -> None:
    st.set_page_config(page_title="PhotoScpec", page_icon="📷", layout="wide")
    st.title("PhotoScpec")
    st.caption("Prepare document photos locally in this session.")
    try:
        service = PhotoScpecService()
        for message in service.config_errors:
            st.warning(message)
        spec, dimensions = dimensions_panel(service, service.list_specs())
    except PhotoScpecError as error:
        show_error(error)
        return
    uploaded = st.file_uploader("2. Upload a JPG or PNG", type=["jpg", "jpeg", "png"])
    if uploaded is None:
        st.session_state.pop("photo_export", None)
        st.session_state.pop("sheet_export", None)
        st.info("Upload a photo to start cropping.")
        return
    source = uploaded.getvalue()
    try:
        info = service.inspect_image(source)
        st.caption(f"Source: {info.width_px} × {info.height_px} px · {info.format} · "
                   f"{info.orientation} · aspect {info.aspect_ratio:.3f}")
        st.subheader("3. Frame and crop")
        a, b = st.columns(2)
        zoom = a.slider("Zoom", 1.0, 5.0, 1.0, 0.01, key="zoom")
        rotation = b.select_slider("Rotate", [0, 90, 180, 270], key="rotation")
        pan_x = st.slider("Pan X", 0.0, 1.0, 0.5, 0.01, key="pan_x")
        pan_y = st.slider("Pan Y", 0.0, 1.0, 0.5, 0.01, key="pan_y")
        frame = crop_frame_request(source, dimensions.width_px, dimensions.height_px,
                                   {"zoom": zoom, "pan_x": pan_x, "pan_y": pan_y,
                                    "rotation": rotation})
        crop = service.calculate_crop(frame)
        cropped = service.create_crop(CropRequest(source, crop, dimensions.width_px,
                                                  dimensions.height_px, rotation))
        preview_bytes = cropped.image
        if st.checkbox("Show positioning guides"):
            guides = service.get_guides(GuideRequest(spec.id if spec else None))
            preview_bytes = guide_preview(cropped.image, guides.guides)
            st.caption(GUIDE_NOTICE)
        st.image(preview_bytes, caption="Cropped preview")
        st.caption(f"Target: {dimensions.width_mm:g} × {dimensions.height_mm:g} mm · "
                   f"{cropped.width_px} × {cropped.height_px} px")
        for warning in cropped.warnings:
            st.warning(warning)
        validation = service.validate_photo(
            ValidationRequest(cropped.image, dimensions.width_px, dimensions.height_px))
        (st.success if validation.valid else st.warning)(
            "Basic output checks passed." if validation.valid else "Review output warnings.")
        for warning in validation.warnings:
            st.warning(warning)
        export_photo_controls(service, cropped, dimensions.dpi)
        print_panel(service, cropped, dimensions, getattr(spec, "printing", None))
    except PhotoScpecError as error:
        show_error(error)


if __name__ == "__main__":
    main()
