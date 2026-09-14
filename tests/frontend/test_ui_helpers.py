from io import BytesIO

from PIL import Image

from photoscpec.interfaces.models import Guide, LayoutRequest
from frontend.streamlit.ui_helpers import (
    guide_preview, keep_ratio_from_height, keep_ratio_from_width, layout_request,
    photo_export_key, sheet_export_key,
)


def test_ratio_callbacks_update_both_directions_without_clamping():
    state = {"custom_ratio": 2.0, "custom_width": 0.02, "custom_height": 1.0}
    keep_ratio_from_width(state)
    assert state["custom_height"] == 0.01
    state["custom_height"] = 405.0
    keep_ratio_from_height(state)
    assert state["custom_width"] == 810.0


def test_layout_request_maps_grid_contract():
    request = layout_request(35, 45, (101.6, 152.4), 6, 2, 3,
                             "2 × 3", None, None, None)
    assert (request.rows, request.columns, request.layout_mode) == (2, 3, "grid")


def test_export_keys_change_with_material_inputs():
    image = b"current-crop"
    first = photo_export_key(image, 300, "PNG")
    assert first != photo_export_key(image, 600, "PNG")
    layout = LayoutRequest(35, 45, 210, 297, 4)
    key = sheet_export_key(image, layout, 300, "PDF", True)
    assert key != sheet_export_key(image, layout, 300, "PNG", True)
    assert key != sheet_export_key(image, LayoutRequest(35, 45, 210, 297, 5), 300,
                                   "PDF", True)


def test_guides_modify_only_preview_copy():
    stream = BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, "PNG")
    cropped = stream.getvalue()
    preview = guide_preview(cropped, [Guide("horizontal", "eyes", position=0.5)])
    assert preview != cropped
    assert photo_export_key(cropped, 300, "PNG") == photo_export_key(cropped, 300, "PNG")
