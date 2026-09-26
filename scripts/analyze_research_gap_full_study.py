from __future__ import annotations

import argparse

from dynnav.evaluation.research_gap_analysis import analyze_full_study_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate the frozen DynNav G1-G5 full-study artifact."
    )
    parser.add_argument(
        "--input",
        default="results/research_gap_program/full_study.json",
    )
    parser.add_argument(
        "--output",
        default="results/research_gap_program/full_study_summary.json",
    )
    args = parser.parse_args()
    analyze_full_study_file(args.input, args.output)


if __name__ == "__main__":
    main()
