#!/usr/bin/env python3
"""Submission preflight: citation keys and V3 abstract numbers vs retained evidence."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def require(condition, message):
    if not condition:
        raise ValueError(message)

def check():
    tex = (ROOT / "main.tex").read_text(encoding="utf-8")
    bib = (ROOT / "references.bib").read_text(encoding="utf-8")
    manifest = json.loads((ROOT / "evidence_manifest.json").read_text(encoding="utf-8"))

    keys = re.findall(r"@\w+\s*\{\s*([^,\s]+)\s*,", bib)
    require(bool(keys) and len(keys) == len(set(keys)), "Missing or duplicate BibTeX entries")
    cited = {
        key.strip()
        for group in re.findall(r"\\cite(?:\[[^\]]*\])*\{([^}]+)\}", tex)
        for key in group.split(",")
    }
    require(cited == set(keys), "Cited/recorded BibTeX keys differ: missing=" +
            repr(sorted(cited - set(keys))) + ", unused=" + repr(sorted(set(keys) - cited)))
    require(r"\bibliography{references}" in tex, "Unexpected bibliography")
    require(r"\documentclass[conference]{IEEEtran}" in tex, "IEEE format changed")

    m = manifest["reviewer_measurement_expansion"]
    require(m["status"] == "retained_success_pinned_publication_artifact", "Missing frozen artifact")
    require(m["scenario_count"] == 96, "Frozen scenario count changed")
    require(m["paired_execution_seeds_per_scenario"] == 250, "Frozen seeds changed")
    require(m["trials_per_planner"] == 24000, "Frozen trials changed")
    aggregate = m["aggregate"]
    base = aggregate["state_only_exact"]["return_infeasible_rate"]
    proposed = aggregate["history_exact"]["return_infeasible_rate"]
    delta = aggregate["history_vs_state_only_exact_scenario_risk_difference"]
    low, high = delta["bootstrap_95"]
    require(abs(proposed - base - delta["mean"]) < 1e-10, "Risk difference mismatch")
    require(delta["sample_size"] == 96, "Wrong scenario-level denominator")
    require(low < delta["mean"] < high, "Invalid interval")

    match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.DOTALL)
    require(match is not None, "No abstract")
    abstract = match.group(1)
    claims = [
        str(m["scenario_count"]) + "-scenario",
        "all " + str(delta["nonworse_scenarios"]) + " scenarios",
        "improves " + str(delta["improved_scenarios"]),
        f"from {base:.3f} to {proposed:.3f}",
        "mean difference of $" + f"{delta['mean']:.3f}" + "$",
        f"[{low:.3f},{high:.3f}]",
    ]
    for claim in claims:
        require(claim in abstract, "Abstract claim differs from evidence manifest: " + claim)
    require("Anonymous Author" in tex, "Anonymized review block missing")
    require(not any(x in tex for x in ("TODO", "TBD", "FIXME")), "Manuscript placeholder remains")
    print(f"PASS: {len(keys)} unique bibliography citations, abstract evidence claims match")
    print(f"PASS: V3 {m['scenario_count']} scenarios, {m['paired_execution_seeds_per_scenario']} paired seeds")
    print("NOTE: this check does not establish novelty, correctness of original data or acceptance")

if __name__ == "__main__":
    try:
        check()
    except (ValueError, FileNotFoundError, KeyError) as e:
        print("FAIL: " + str(e), file=sys.stderr)
        sys.exit(1)
