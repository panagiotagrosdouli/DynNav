from __future__ import annotations

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from causal_risk import CausalNode, NavigationSCM, NodeType


class CausalRiskTests(unittest.TestCase):
    def test_custom_nodes_are_evaluated_topologically(self) -> None:
        scm = NavigationSCM()
        scm.add_node(CausalNode("late_child", parents=["late_parent"], structural_eq=lambda p, n: p["late_parent"] + n))
        scm.add_node(CausalNode("late_parent", NodeType.EXOGENOUS, structural_eq=lambda p, n: n))

        values = scm.observational_query({"late_parent": 2.0, "late_child": 3.0})
        self.assertEqual(values["late_child"], 5.0)

    def test_cycles_and_unknown_parents_are_rejected(self) -> None:
        scm = NavigationSCM()
        scm.add_node(CausalNode("cycle_a", parents=["cycle_b"]))
        scm.add_node(CausalNode("cycle_b", parents=["cycle_a"]))
        with self.assertRaisesRegex(ValueError, "cycle"):
            scm.observational_query({})

        incomplete = NavigationSCM()
        incomplete.add_node(CausalNode("orphan", parents=["missing"]))
        with self.assertRaisesRegex(ValueError, "unknown parent"):
            incomplete.observational_query({})

    def test_counterfactual_rejects_unknown_interventions(self) -> None:
        scm = NavigationSCM()
        with self.assertRaisesRegex(ValueError, "unknown intervention"):
            scm.counterfactual_query({}, {"misspelled_node": 0.0})

    def test_root_cause_ranking_uses_paired_noise_and_is_reproducible(self) -> None:
        scm = NavigationSCM()
        noise = {
            "sensor_noise": 1.2,
            "localization_error": 0.3,
            "map_accuracy": -0.1,
            "obstacle_detection": 0.2,
            "path_risk": 0.1,
            "collision": 0.0,
        }
        first = scm.root_cause_ranking(noise, n_samples=20)
        second = scm.root_cause_ranking(noise, n_samples=20)
        self.assertEqual(first, second)
        self.assertEqual({name for name, _ in first}, {
            "sensor_noise", "localization_error", "map_accuracy",
            "obstacle_detection", "path_risk",
        })


if __name__ == "__main__":
    unittest.main()
