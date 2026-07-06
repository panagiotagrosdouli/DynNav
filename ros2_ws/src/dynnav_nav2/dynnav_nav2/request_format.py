"""String formatting helpers for planning requests."""

from __future__ import annotations


def parse_cell(raw: str) -> tuple[int, int]:
    x_raw, y_raw = raw.strip().split(":", maxsplit=1)
    return int(x_raw), int(y_raw)


def parse_request(raw: str) -> tuple[tuple[int, int], tuple[int, int]]:
    parts = raw.split(";", maxsplit=1)
    if len(parts) != 2:
        raise ValueError("request must contain start and goal")
    return parse_cell(parts[0]), parse_cell(parts[1])


def format_response(success: bool, path: list[tuple[int, int]], message: str) -> str:
    if not success:
        return f"FAILED: {message}"
    return "OK: " + " -> ".join(f"({x},{y})" for x, y in path)
