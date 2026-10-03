"""Frozen V4 model-misspecification conditions.

The condition file is data, not an outcome-tuned parameter source. It separates
the true O2 generative sensor model from the model assumed by the planner.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class V4MisspecificationCondition:
    condition_id: str
    assumed_sensitivity: float
    assumed_specificity: float
    assumed_arming_offset: float
    role: str

    def validate(self) -> None:
        if not self.condition_id:
            raise ValueError("condition_id cannot be empty")
        if not 0.0 <= self.assumed_sensitivity <= 1.0:
            raise ValueError("assumed_sensitivity must be in [0, 1]")
        if not 0.0 <= self.assumed_specificity <= 1.0:
            raise ValueError("assumed_specificity must be in [0, 1]")
        if not -1.0 <= self.assumed_arming_offset <= 1.0:
            raise ValueError("assumed_arming_offset must be in [-1, 1]")


@dataclass(frozen=True)
class V4MisspecificationMatrix:
    true_regime: str
    true_sensitivity: float
    true_specificity: float
    conditions: tuple[V4MisspecificationCondition, ...]

    def validate(self) -> None:
        if self.true_regime != "O2":
            raise ValueError("V4 misspecification matrix must use true O2 regime")
        if not 0.0 <= self.true_sensitivity <= 1.0:
            raise ValueError("true_sensitivity must be in [0, 1]")
        if not 0.0 <= self.true_specificity <= 1.0:
            raise ValueError("true_specificity must be in [0, 1]")
        if not self.conditions:
            raise ValueError("at least one misspecification condition is required")
        ids: set[str] = set()
        for condition in self.conditions:
            condition.validate()
            if condition.condition_id in ids:
                raise ValueError(
                    f"duplicate misspecification id: {condition.condition_id}"
                )
            ids.add(condition.condition_id)
        if "M0_correct" not in ids:
            raise ValueError("M0_correct condition is required")


def load_misspecification_matrix(
    path: str | Path = "benchmarks/v4/misspecification.json",
) -> V4MisspecificationMatrix:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    conditions = tuple(
        V4MisspecificationCondition(
            condition_id=str(item["id"]),
            assumed_sensitivity=float(item["assumed_sensitivity"]),
            assumed_specificity=float(item["assumed_specificity"]),
            assumed_arming_offset=float(item["assumed_arming_offset"]),
            role=str(item["role"]),
        )
        for item in payload["conditions"]
    )
    matrix = V4MisspecificationMatrix(
        true_regime=str(payload["true_regime"]),
        true_sensitivity=float(payload["true_sensitivity"]),
        true_specificity=float(payload["true_specificity"]),
        conditions=conditions,
    )
    matrix.validate()
    return matrix
