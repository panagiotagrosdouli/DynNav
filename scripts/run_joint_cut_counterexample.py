#!/usr/bin/env python3
"""Run the planner-level joint-cut approximation counterexample."""
from __future__ import annotations

import argparse

from dynnav.experiments.joint_cut_counterexample import (
    run_joint_cut_counterexample,
    write_joint_cut_counterexample_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="results/joint_cut_counterexample")
    args = parser.parse_args()
    records = run_joint_cut_counterexample()
    write_joint_cut_counterexample_artifacts(records, args.out_dir)


if __name__ == "__main__":
    main()
