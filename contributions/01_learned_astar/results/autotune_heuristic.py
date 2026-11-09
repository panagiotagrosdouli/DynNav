"""Historical C01 online fine-tuning experiment (SYNTHETIC fixed 40x40 grid).

Requires an existing C01 11-feature state_dict checkpoint. Always copies
the checkpoint into --out-dir before online adaptation; NEVER mutates the
original research artifact. Its path labels are not real-world robot data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
C01 = Path(__file__).resolve().parents[1]
for directory in (ROOT / "core", C01 / "code"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from astar_learned_heuristic import (
    make_grid, astar_classic, astar_learned,
    LearnedHeuristicWrapper, compute_true_remaining_cost,
)
from heuristic_logger import HeuristicLogger
from online_update_heuristic import online_update


def run_one_iteration(
    iteration: int,
    model_path: Path,
    log_path: Path,
    *,
    epochs: int = 1,
) -> dict:
    grid = make_grid()
    start, goal = (1, 1), (35, 35)
    classic, expansions_classic = astar_classic(grid, start, goal)
    if classic is None:
        raise RuntimeError("Fixed grid baseline is unexpectedly unreachable")
    true_cost = compute_true_remaining_cost(classic)
    logger = HeuristicLogger(str(log_path), true_cost_map=true_cost)
    learned = LearnedHeuristicWrapper(model_path=str(model_path), logger=logger)
    planned, expansions_learned = astar_learned(grid, start, goal, learned)
    if planned is None:
        raise RuntimeError("Learned search failed to return a route")
    logger.save()
    if not log_path.is_file():
        raise RuntimeError("No new training samples were logged")
    online_update(
        model_path=str(model_path), log_path=str(log_path),
        epochs=epochs, lr=1e-4, batch_size=128,
    )
    return {
        "iteration": iteration,
        "classic_path_len": len(classic),
        "classic_expansions": expansions_classic,
        "learned_path_len": len(planned),
        "learned_expansions": expansions_learned,
        "expansion_ratio": expansions_learned / expansions_classic,
        "delta_path": len(planned) - len(classic),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=C01 / "models" / "heuristic_net_rich.pt")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=1)
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()
    if args.iterations < 1 or args.epochs < 1:
        parser.error("iterations/epochs must be positive")
    original = args.model.resolve()
    if not original.is_file():
        raise FileNotFoundError(original)
    outdir = args.out_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    model = outdir / "heuristic_net_rich_adapted.pt"
    if original == model:
        raise ValueError("Output model path must differ from source checkpoint")
    input_hash = hashlib.sha256(original.read_bytes()).hexdigest()
    shutil.copyfile(original, model)
    logs = outdir / "heuristic_logs_adaptation.npz"
    if logs.exists():
        raise FileExistsError(f"Refusing to append to existing run's logs: {logs}")
    rows = [
        run_one_iteration(it, model, logs, epochs=args.epochs)
        for it in range(args.iterations)
    ]
    target = outdir / "autotune_results.csv"
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    assert hashlib.sha256(original.read_bytes()).hexdigest() == input_hash
    print(f"SYNTHETIC ONLY: original checkpoint unchanged: {original}")
    print(f"Original SHA256: {input_hash}; adapted copy: {model}")
    print(f"Saved measured synthetic rows: {target}")


if __name__ == "__main__":
    main()
