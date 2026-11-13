import importlib.util
from pathlib import Path
import sys

import numpy as np

path = Path(__file__).resolve().parents[1] / "multimodal_failure_explainer.py"
spec = importlib.util.spec_from_file_location("c20_fail_closed", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_actual_failure_report_does_not_invent_causes_or_vlm_evidence():
    event = module.FailureEvent(
        module.FailureType.COLLISION,
        3.0,
        (1.0, 2.0),
        (0.2, 0.0),
        frame=np.zeros((10, 10, 3)),
        sensor_readings={"min_obstacle_dist": 0.15},
    )
    report = module.MultimodalFailureExplainer(use_vlm=True, use_causal=True).explain(event)
    assert report.root_causes == []
    assert report.scene_description == "Scene analysis unavailable."
    assert report.confidence == 0.0
    assert report.to_dict()["confidence_status"] == "unavailable_uncalibrated"
    assert "causal contribution" not in report.to_markdown()
