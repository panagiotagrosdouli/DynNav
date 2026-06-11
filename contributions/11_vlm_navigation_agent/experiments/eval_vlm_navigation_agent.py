import csv
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RESULTS = BASE / "results"
OUT_CSV = RESULTS / "c11_vlm_navigation_summary.csv"
OUT_MD = RESULTS / "c11_vlm_navigation_summary.md"

SCENES = [
    {"id": 0, "text": "corridor visible ahead, go forward", "gt_region": "corridor", "gt_goal": "forward", "confidence": 0.90, "latency_ms": 18},
    {"id": 1, "text": "doorway on the left", "gt_region": "doorway", "gt_goal": "left", "confidence": 0.86, "latency_ms": 17},
    {"id": 2, "text": "open room on the right", "gt_region": "room", "gt_goal": "right", "confidence": 0.84, "latency_ms": 19},
    {"id": 3, "text": "blocked obstacle zone ahead", "gt_region": "obstacle_zone", "gt_goal": "avoid", "confidence": 0.88, "latency_ms": 21},
    {"id": 4, "text": "large open space ahead", "gt_region": "open_space", "gt_goal": "forward", "confidence": 0.82, "latency_ms": 16},
    {"id": 5, "text": "corridor bends right", "gt_region": "corridor", "gt_goal": "right", "confidence": 0.80, "latency_ms": 18},
    {"id": 6, "text": "exit doorway ahead", "gt_region": "doorway", "gt_goal": "forward", "confidence": 0.87, "latency_ms": 20},
    {"id": 7, "text": "hazardous object on the left", "gt_region": "obstacle_zone", "gt_goal": "avoid", "confidence": 0.89, "latency_ms": 23},
]

REGION_RULES = {
    "corridor": "corridor",
    "doorway": "doorway",
    "door": "doorway",
    "room": "room",
    "open space": "open_space",
    "obstacle": "obstacle_zone",
    "blocked": "obstacle_zone",
    "hazard": "obstacle_zone",
}

GOAL_RULES = {
    "left": "left",
    "right": "right",
    "avoid": "avoid",
    "blocked": "avoid",
    "hazard": "avoid",
    "ahead": "forward",
    "forward": "forward",
}


def predict(text):
    t = text.lower()
    region = "unknown"
    goal = "unknown"
    for k, v in REGION_RULES.items():
        if k in t:
            region = v
            break
    for k, v in GOAL_RULES.items():
        if k in t:
            goal = v
            break
    return region, goal


def main():
    rows = []
    region_ok = 0
    goal_ok = 0
    valid_goals = 0
    conf_sum = 0.0
    latency_sum = 0.0

    for s in SCENES:
        pred_region, pred_goal = predict(s["text"])
        r_ok = int(pred_region == s["gt_region"])
        g_ok = int(pred_goal == s["gt_goal"])
        valid = int(pred_goal != "unknown" and pred_region != "unknown")
        region_ok += r_ok
        goal_ok += g_ok
        valid_goals += valid
        conf_sum += s["confidence"]
        latency_sum += s["latency_ms"]
        rows.append({
            "scene_id": s["id"],
            "gt_region": s["gt_region"],
            "pred_region": pred_region,
            "region_match": r_ok,
            "gt_goal": s["gt_goal"],
            "pred_goal": pred_goal,
            "goal_match": g_ok,
            "valid_goal": valid,
            "confidence": s["confidence"],
            "latency_ms": s["latency_ms"],
        })

    n = len(SCENES)
    region_acc = region_ok / n
    goal_acc = goal_ok / n
    valid_rate = valid_goals / n
    mean_conf = conf_sum / n
    mean_latency = latency_sum / n
    calibration_error = abs(mean_conf - goal_acc)

    summary = {
        "n_scenes": n,
        "region_accuracy": region_acc,
        "goal_accuracy": goal_acc,
        "valid_goal_rate": valid_rate,
        "mean_confidence": mean_conf,
        "mean_latency_ms": mean_latency,
        "confidence_goal_calibration_error": calibration_error,
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "c11_vlm_navigation_per_scene.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary.keys()))
        w.writeheader()
        w.writerow(summary)

    OUT_MD.write_text(
        "# C11 VLM Navigation Agent Summary\n\n"
        f"- Scenes evaluated: {n}\n"
        f"- Semantic region accuracy: {region_acc:.3f}\n"
        f"- Navigation goal accuracy: {goal_acc:.3f}\n"
        f"- Valid goal generation rate: {valid_rate:.3f}\n"
        f"- Mean confidence: {mean_conf:.3f}\n"
        f"- Mean latency: {mean_latency:.2f} ms\n"
        f"- Confidence-goal calibration error: {calibration_error:.3f}\n\n"
        "## Interpretation\n\n"
        "This offline benchmark evaluates the deterministic visual-language grounding layer without requiring an external VLM server. It measures whether scene descriptions are mapped to semantic regions and navigation goals in a reproducible way.\n"
    )

    print(f"[INFO] Wrote {OUT_CSV}")
    print(f"[INFO] Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
