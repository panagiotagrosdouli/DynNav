from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from dynnav.experiments.v4_information_value_counterexample import (
    run_information_value_counterexample,
    write_information_value_counterexample,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the V4 future-information approximation counterexample."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "results/v4_information_value_counterexample/result.json"
        ),
    )
    args = parser.parse_args()

    result = run_information_value_counterexample()
    write_information_value_counterexample(args.output)
    print(
        json.dumps(
            {
                "status": "development_only_not_publication_evidence",
                **asdict(result),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
