import unittest
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from topo_semantic_map import TopologicalSemanticMap


class TopologicalSemanticMapTests(unittest.TestCase):
    def test_label_stub_is_reproducible_and_graph_path_updates(self):
        graph = TopologicalSemanticMap()
        a = graph.add_node("a", (0.0, 0.0), embedding=np.array([1.0, 0.0]))
        b = graph.add_node("b", (1.0, 0.0), embedding=np.array([0.0, 1.0]))
        graph.add_edge(a, b, weight=2.0)
        self.assertEqual(graph.embed_label_stub("kitchen").tolist(),
                         graph.embed_label_stub("kitchen").tolist())
        self.assertEqual(graph.plan(a, b), ([a, b], 2.0))
        graph.invalidate_edge(a, b)
        self.assertTrue(np.isinf(graph.plan(a, b)[1]))
        restored = TopologicalSemanticMap.from_dict(graph.to_dict())
        self.assertTrue(np.isinf(restored.plan(a, b)[1]))

    def test_rejects_invalid_graph_and_query_inputs(self):
        graph = TopologicalSemanticMap()
        a = graph.add_node("a", (0.0, 0.0))
        with self.assertRaises(ValueError):
            graph.add_edge(a, 99)
        with self.assertRaises(ValueError):
            graph.add_edge(a, a, weight=float("nan"))
        with self.assertRaises(ValueError):
            graph.ground_query(np.array([1.0]), top_k=0)


if __name__ == "__main__":
    unittest.main()
