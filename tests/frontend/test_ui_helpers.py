from frontend.ui_helpers import keep_ratio_from_height, keep_ratio_from_width, layout_request


def test_ratio_callbacks_update_both_directions():
    state = {"custom_ratio": 2.0, "custom_width": 630.0, "custom_height": 810.0}
    keep_ratio_from_width(state)
    assert state["custom_height"] == 315.0
    state["custom_height"] = 405.0
    keep_ratio_from_height(state)
    assert state["custom_width"] == 810.0


def test_layout_request_maps_fixed_grid_and_orientation():
    request = layout_request(35, 45, (101.6, 152.4), 6, 2, 3,
                             "2 × 3", None, None, None)
    assert (request.rows, request.columns, request.layout_mode) == (2, 3, "custom")
    assert request.orientation is None


def test_layout_request_maps_custom_rows_and_columns():
    request = layout_request(35, 45, (210, 297), 8, 1, 4,
                             "Custom", 4, 2, "landscape")
    assert (request.rows, request.columns) == (4, 2)
    assert request.orientation == "landscape"
