"""Shared interfaces for DynNav contribution modules.

The types in this module deliberately distinguish generated artifacts from
validated evidence.  A successful synthetic run must not be promoted to a
ROS 2, hardware, dataset, neural-training, or formal-safety claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class MaturityStatus(StrEnum):
    IMPLEMENTED = "Implemented"
    RESEARCH_PROTOTYPE = "Research Prototype"
    EXPERIMENTAL = "Experimental"
    SYNTHETIC_VALIDATION = "Synthetic Validation"
    DATASET_VALIDATION = "Dataset Validation"
    SIMULATION_VALIDATION = "Simulation Validation"
    DOCUMENTATION_CONCEPT = "Documentation Concept"
    PLANNED = "Planned"
    MISSING_IMPLEMENTATION = "Missing Implementation"
    DEPRECATED = "Deprecated"
    DUPLICATE = "Duplicate"
    ROS2_PENDING = "ROS 2 Validation Pending"
    HARDWARE_REQUIRED = "Hardware Validation Required"


class EvidenceKind(StrEnum):
    CONCEPTUAL = "conceptual"
    FIXTURE = "deterministic_fixture"
    SYNTHETIC = "synthetic_validation"
    DATASET = "dataset_validation"
    SIMULATION = "simulation_validation"
    ROS2 = "ros2_validation"
    HARDWARE = "hardware_validation"
    FORMAL = "formal_claim"


@dataclass(frozen=True)
class ContributionMetadata:
    id: str
    slug: str
    title: str
    category: str
    status: MaturityStatus
    directory: Path
    integrates_with: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContributionConfig:
    contribution_id: str
    seed: int
    values: Mapping[str, Any]


@dataclass(frozen=True)
class EvidenceRecord:
    kind: EvidenceKind
    source: str
    claim: str
    reproducible: bool
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class VisualizationArtifact:
    path: Path
    source_data: Path | None
    generator: str
    seed: int | None
    maturity: MaturityStatus
    alt_text: str


@dataclass
class ContributionResult:
    contribution_id: str
    status: str
    metrics: dict[str, float] = field(default_factory=dict)
    artifacts: list[VisualizationArtifact] = field(default_factory=list)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ExperimentManifest:
    contribution_id: str
    seed: int
    git_commit: str
    source_config: str
    resolved_config: Mapping[str, Any]
    environment: Mapping[str, str]
    outputs: tuple[str, ...]
    status: str
    failure: str | None = None


@dataclass(frozen=True)
class ExplanationRecord:
    contribution_id: str
    summary: str
    evidence_ids: tuple[str, ...]
    uncertainty: float | None
    counterfactual: str | None = None
