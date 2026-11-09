"""Compatibility exports for the C11 VLM goal-validation module."""

from dynnav.researcher.vlm_goal_validator import (
    GoalDecision,
    GoalValidationReport,
    ValidationConfig,
    validate_vlm_goal,
)

__all__ = ["GoalDecision", "GoalValidationReport", "ValidationConfig", "validate_vlm_goal"]
