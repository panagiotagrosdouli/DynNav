"""Deterministic publication outputs generated from retained V4 analysis JSON.

No empirical value is hard-coded here. Tables and figures are rendered directly
from the frozen analysis artifact so manuscript-facing numbers remain traceable
to retained raw trials.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt


def _fmt(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "--"
    return f"{float(value):.{digits}f}"


def _interval_text(payload: dict[str, object] | None) -> str:
    if payload is None:
        return "--"
    return (
        f"{_fmt(float(payload['estimate']))} "
        f"[{_fmt(float(payload['lower']))}, "
        f"{_fmt(float(payload['upper']))}]"
    )


def primary_table_tex(analysis: dict[str, object]) -> str:
    comparisons = analysis["comparisons"]
    if not isinstance(comparisons, dict):
        raise ValueError("analysis comparisons must be a mapping")

    rows = []
    for key, result in comparisons.items():
        if not isinstance(result, dict):
            raise ValueError(f"invalid comparison payload: {key}")
        baseline = str(result["baseline"])
        rows.append(
            (
                baseline,
                _interval_text(result.get("mission_failure_difference")),
                _interval_text(result.get("operational_failure_difference")),
                _interval_text(result.get("conditional_return_risk_difference")),
                _interval_text(result.get("conditional_brier_difference")),
                _interval_text(result.get("conditional_path_length_difference")),
            )
        )

    lines = [
        r"\begin{tabular}{lccccc}",
        r"\toprule",
        (
            r"Baseline & $\Delta$ mission fail & $\Delta$ operational fail "
            r"& $\Delta$ return risk & $\Delta$ Brier & $\Delta$ path \\"
        ),
        r"\midrule",
    ]
    for row in rows:
        escaped = row[0].replace("_", r"\_")
        lines.append(
            f"{escaped} & {row[1]} & {row[2]} & {row[3]} & {row[4]} & {row[5]} \\\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            "",
        ]
    )
    return "\n".join(lines)


def calibration_table_tex(analysis: dict[str, object]) -> str:
    metrics = analysis["calibration_metrics"]
    if not isinstance(metrics, dict):
        raise ValueError("calibration_metrics must be a mapping")

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Planner & Brier & Cal.-in-large & ECE & $n$ \\",
        r"\midrule",
    ]
    for planner, payload in metrics.items():
        if not isinstance(payload, dict):
            raise ValueError(f"invalid calibration payload: {planner}")
        escaped = str(planner).replace("_", r"\_")
        lines.append(
            f"{escaped} & "
            f"{_fmt(float(payload['brier_score']))} & "
            f"{_fmt(float(payload['calibration_in_the_large']))} & "
            f"{_fmt(float(payload['expected_calibration_error']))} & "
            f"{int(payload['count'])} \\\\"
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", ""])
    return "\n".join(lines)


def render_calibration_figure(
    analysis: dict[str, object],
    output_path: str | Path,
) -> None:
    calibration = analysis["calibration"]
    if not isinstance(calibration, dict):
        raise ValueError("calibration must be a mapping")

    selected = (
        "belief",
        "detector_as_truth",
        "prior_only",
        "fixed_marginal_exact",
    )
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.plot([0.0, 1.0], [0.0, 1.0], linestyle="--", label="perfect calibration")

    for planner in selected:
        raw_bins = calibration.get(planner)
        if not isinstance(raw_bins, list):
            continue
        x: list[float] = []
        y: list[float] = []
        for item in raw_bins:
            if not isinstance(item, dict):
                continue
            prediction = item.get("mean_prediction")
            frequency = item.get("empirical_frequency")
            if prediction is None or frequency is None:
                continue
            x.append(float(prediction))
            y.append(float(frequency))
        if x:
            ax.plot(x, y, marker="o", label=planner.replace("_", " "))

    ax.set_xlabel("Predicted safe-return probability")
    ax.set_ylabel("Empirical safe-return frequency")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.legend()
    fig.tight_layout()
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def render_v4_publication_outputs(
    analysis_path: str | Path,
    output_dir: str | Path,
) -> dict[str, object]:
    source = Path(analysis_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    analysis = json.loads(source.read_text(encoding="utf-8"))
    primary = destination / "table_v4_primary.tex"
    calibration_table = destination / "table_v4_calibration.tex"
    calibration_figure = destination / "figure_v4_calibration.png"

    primary.write_text(primary_table_tex(analysis), encoding="utf-8")
    calibration_table.write_text(
        calibration_table_tex(analysis),
        encoding="utf-8",
    )
    render_calibration_figure(analysis, calibration_figure)

    files = (primary, calibration_table, calibration_figure)
    manifest = {
        "input_analysis": str(source),
        "input_analysis_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "outputs": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }
    (destination / "publication_output_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
