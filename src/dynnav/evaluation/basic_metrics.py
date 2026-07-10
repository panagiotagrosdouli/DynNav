from __future__ import annotations


def path_length(path: list[tuple[int, int]]) -> int:
    return max(0, len(path) - 1)


def total_signal(values: list[float]) -> float:
    return float(sum(values))


__all__ = ["path_length", "total_signal"]
