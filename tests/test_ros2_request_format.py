from ros2_ws.src.dynnav_nav2.dynnav_nav2.request_format import (
    format_response,
    parse_cell,
    parse_request,
)


def test_parse_cell():
    assert parse_cell("2:3") == (2, 3)


def test_parse_request():
    assert parse_request("0:1;4:5") == ((0, 1), (4, 5))


def test_format_response_success():
    assert format_response(True, [(0, 0), (1, 0)], "ok") == "OK: (0,0) -> (1,0)"


def test_format_response_failure():
    assert format_response(False, [], "no path") == "FAILED: no path"
