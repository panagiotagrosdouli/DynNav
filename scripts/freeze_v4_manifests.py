from __future__ import annotations

from pathlib import Path

from dynnav.experiments.v4_scenario_manifest import (
    V4_DEVELOPMENT_SEED,
    V4_HELDOUT_SEED,
    V4_VALIDATION_SEED,
    development_suite,
    heldout_suite,
    validation_suite,
    write_manifest,
)


def main() -> None:
    root = Path("benchmarks/v4")
    write_manifest(
        development_suite(),
        root / "development.json",
        split="development",
        seed=V4_DEVELOPMENT_SEED,
    )
    write_manifest(
        validation_suite(),
        root / "validation.json",
        split="validation",
        seed=V4_VALIDATION_SEED,
    )
    write_manifest(
        heldout_suite(),
        root / "heldout.json",
        split="heldout",
        seed=V4_HELDOUT_SEED,
    )


if __name__ == "__main__":
    main()
