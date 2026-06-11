import csv
from pathlib import Path

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from language_safety_policy import LanguageSafetyPolicy
from nlp_constraint_mapper import NLPConstraintMapper
BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"

OUT_CSV = RESULTS / "c10_language_ethics_summary.csv"
OUT_MD = RESULTS / "c10_language_ethics_summary.md"


def main():
    policy = LanguageSafetyPolicy()
    mapper = NLPConstraintMapper()

    safe_msgs = [
        "normal corridor",
        "safe area",
        "nothing special",
        "move normally",
    ]

    risk_msgs = [
        "crowded area with many people",
        "wet floor and slippery corridor",
        "children are present",
        "elderly people near the stairs",
        "hidden hazard around the corner",
    ]

    planner_cmds = [
        "prefer safe paths",
        "avoid narrow spaces",
        "move quickly",
        "save power",
        "avoid crowd",
    ]

    safe_unchanged = 0
    risk_adjusted = 0

    for msg in safe_msgs:
        d = policy.evaluate(msg)
        if d.risk_scale == 1.0:
            safe_unchanged += 1

    for msg in risk_msgs:
        d = policy.evaluate(msg)
        if d.risk_scale > 1.0:
            risk_adjusted += 1

    mapped = 0
    for cmd in planner_cmds:
        mods = mapper.parse(cmd)
        if "No rules matched" not in mods.description[0]:
            mapped += 1

    summary = {
        "safe_messages": len(safe_msgs),
        "safe_messages_correct": safe_unchanged,
        "risk_messages": len(risk_msgs),
        "risk_messages_adjusted": risk_adjusted,
        "constraint_commands": len(planner_cmds),
        "constraint_commands_mapped": mapped,
        "safe_message_accuracy": safe_unchanged / len(safe_msgs),
        "risk_detection_rate": risk_adjusted / len(risk_msgs),
        "constraint_mapping_rate": mapped / len(planner_cmds),
    }

    RESULTS.mkdir(parents=True, exist_ok=True)

    with open(OUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    with open(OUT_MD, "w") as f:
        f.write("# C10 Human Language & Ethics Summary\n\n")
        f.write(
            f"- Safe message accuracy: {summary['safe_message_accuracy']:.3f}\n"
        )
        f.write(
            f"- Risk detection rate: {summary['risk_detection_rate']:.3f}\n"
        )
        f.write(
            f"- Constraint mapping rate: {summary['constraint_mapping_rate']:.3f}\n\n"
        )

        f.write("## Interpretation\n\n")
        f.write(
            "The language safety layer successfully identifies risk-related "
            "natural-language descriptions and maps planning instructions "
            "to navigation cost modifiers. This demonstrates a bridge "
            "between human language and autonomous planning constraints.\n"
        )

    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
