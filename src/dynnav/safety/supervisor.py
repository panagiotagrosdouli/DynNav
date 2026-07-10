from __future__ import annotations

SAFETY_STATES = ("NORMAL", "CAUTION", "REROUTE", "SLOW_DOWN", "STOP", "MISSION_ABORT")


def supervisor_state(risk: float, uncertainty: float, recoverability: float, path_blocked: bool = False) -> str:
    if path_blocked or risk > 0.86 or recoverability < 0.08:
        return "REROUTE"
    if risk > 0.70:
        return "SLOW_DOWN"
    if risk > 0.55 or uncertainty > 0.65 or recoverability < 0.25:
        return "CAUTION"
    return "NORMAL"


__all__ = ["SAFETY_STATES", "supervisor_state"]
