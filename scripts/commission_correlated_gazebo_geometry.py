from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.correlated_gazebo_commissioning import commission_second_blocker


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--return-snapshot", type=Path, required=True)
    parser.add_argument("--forward-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = commission_second_blocker(
        return_snapshot_path=args.return_snapshot,
        forward_snapshot_path=args.forward_snapshot,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
