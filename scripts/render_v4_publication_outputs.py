from __future__ import annotations

import argparse
import json
from pathlib import Path

from dynnav.experiments.v4_publication import render_v4_publication_outputs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render deterministic V4 publication tables/figures."
    )
    parser.add_argument("analysis", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/v4_publication"),
    )
    args = parser.parse_args()

    manifest = render_v4_publication_outputs(
        args.analysis,
        args.output_dir,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
