from pathlib import Path
import csv
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results'


def main():
    RESULTS.mkdir(exist_ok=True)
    planners = ['dijkstra', 'astar', 'risk_astar', 'uncertainty_astar', 'recoverability_astar']
    rows = []
    for planner in planners:
        subprocess.run([sys.executable, str(ROOT / 'scripts/run_all.py')], check=True)
        summary = json.loads((RESULTS / 'metrics/summary.json').read_text())
        summary['planner'] = planner
        rows.append(summary)
    (RESULTS / 'metrics').mkdir(parents=True, exist_ok=True)
    with (RESULTS / 'metrics/benchmark_summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    (RESULTS / 'reports').mkdir(parents=True, exist_ok=True)
    (RESULTS / 'reports/benchmark_report.md').write_text('# Benchmark Report\n\nSynthetic deterministic benchmark scaffold. No state-of-the-art claims.\n\n```json\n' + json.dumps(rows, indent=2) + '\n```\n')
    print('Benchmark outputs saved to results/metrics/benchmark_summary.csv and results/reports/benchmark_report.md')


if __name__ == '__main__':
    main()
