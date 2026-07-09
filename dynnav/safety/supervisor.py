from dataclasses import dataclass
from dynnav.core.types import SafetyState

@dataclass
class SafetyDecision:
    state: SafetyState; reason: str

def decide(risk,uncertainty,recoverability,blocked,collision=False):
    if collision: return SafetyDecision(SafetyState.MISSION_ABORT,'collision')
    if blocked: return SafetyDecision(SafetyState.REROUTE,'path_blocked')
    if risk>0.82 or recoverability<0.12: return SafetyDecision(SafetyState.STOP,'high_risk_or_low_recoverability')
    if risk>0.62: return SafetyDecision(SafetyState.SLOW_DOWN,'elevated_risk')
    if uncertainty>0.55 or recoverability<0.25: return SafetyDecision(SafetyState.CAUTION,'uncertainty_or_recoverability')
    return SafetyDecision(SafetyState.NORMAL,'nominal')
