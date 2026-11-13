"""
Contribution 17: Topological + Semantic Maps
=============================================
Builds and navigates a graph of semantic zones (rooms, corridors, doorways)
rather than a dense metric occupancy grid.  Nodes in the graph represent
named semantic regions; edges represent traversable transitions.

Open-vocabulary grounding: CLIP embeddings (or a stub) score how well
a visual observation matches a semantic label, enabling instruction following
such as "go to the kitchen" without a pre-built map.

Research Question (RQ-Topo): Does a topological-semantic representation
reduce planning complexity and improve long-horizon navigation success rate
in large unknown environments?

References:
    Savinov et al. (2018) "Semi-parametric Topological Memory for Navigation"
    Gu et al. (2022) "Open-vocabulary Mobile Manipulation via Embodied Visual Matching"
"""

from __future__ import annotations

import logging
import hashlib
import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Graph nodes and edges
# ---------------------------------------------------------------------------

@dataclass
class SemanticNode:
    node_id: int
    label: str                     # e.g. "kitchen", "corridor_A", "doorway_1"
    centroid_xy: tuple[float, float]  # approximate metric centroid
    embedding: Optional[np.ndarray] = None   # CLIP or learned embedding
    properties: dict = field(default_factory=dict)

    def similarity(self, query_emb: np.ndarray) -> float:
        """Cosine similarity to a query embedding."""
        if self.embedding is None:
            return 0.0
        a = np.asarray(self.embedding, dtype=float)
        b = np.asarray(query_emb, dtype=float)
        if a.ndim != 1 or b.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError('Invalid semantic embedding: dimension mismatch or non-finite values')
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        a = a / np.linalg.norm(a)
        b = b / np.linalg.norm(b)
        return float(np.dot(a, b))


@dataclass
class SemanticEdge:
    src: int
    dst: int
    weight: float = 1.0            # traversal cost
    passable: bool = True
    transition_type: str = "open"  # "open" | "door" | "narrow"


# ---------------------------------------------------------------------------
# Topological map
# ---------------------------------------------------------------------------

class TopologicalSemanticMap:
    """
    A sparse graph of semantic zones with metric centroids and embeddings.
    Supports:
        - Node creation from observations
        - Open-vocabulary search (find node closest to a text/visual query)
        - Dijkstra path planning over the graph
        - Dynamic edge invalidation (obstacle discovered → mark impassable)
    """

    def __init__(self):
        self.nodes: dict[int, SemanticNode] = {}
        self.edges: list[SemanticEdge] = []
        self._adj: dict[int, list[SemanticEdge]] = {}
        self._next_id = 0

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_node(self, label: str,
                 centroid_xy: tuple[float, float],
                 embedding: Optional[np.ndarray] = None,
                 **props) -> int:
        nid = self._next_id
        self._next_id += 1
        self.nodes[nid] = SemanticNode(nid, label, centroid_xy,
                                        embedding, props)
        self._adj[nid] = []
        logger.debug("Added node %d: %s at %s", nid, label, centroid_xy)
        return nid

    def add_edge(self, src: int, dst: int,
                 weight: float = 1.0,
                 bidirectional: bool = True,
                 transition_type: str = "open") -> None:
        if src not in self.nodes or dst not in self.nodes:
            raise ValueError('Cannot add semantic edge to nonexistent node')
        if not math.isfinite(weight) or weight < 0:
            raise ValueError('Semantic graph requires finite nonnegative traversal cost')
        e = SemanticEdge(src, dst, weight, True, transition_type)
        self.edges.append(e)
        self._adj[src].append(e)
        if bidirectional:
            e2 = SemanticEdge(dst, src, weight, True, transition_type)
            self.edges.append(e2)
            self._adj[dst].append(e2)

    def invalidate_edge(self, src: int, dst: int) -> None:
        """Mark an edge impassable (obstacle discovered)."""
        for e in self._adj.get(src, []):
            if e.dst == dst:
                e.passable = False
                logger.info("Edge %d→%d invalidated", src, dst)

    # ------------------------------------------------------------------
    # Open-vocabulary grounding
    # ------------------------------------------------------------------

    def ground_query(self, query_embedding: np.ndarray,
                     top_k: int = 3) -> list[tuple[int, str, float]]:
        """
        Find top-k nodes whose embedding best matches a query.
        Returns list of (node_id, label, similarity).
        """
        scored = [
            (nid, node.label, node.similarity(query_embedding))
            for nid, node in self.nodes.items()
        ]
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]

    def embed_label_stub(self, label: str) -> np.ndarray:
        """
        Stub CLIP embedding: uses a deterministic hash of the label string.
        Replace with: clip_model.encode_text(label).cpu().numpy()
        """
        # Python hash() is process-salted; SHA256 keeps stub grounding stable
        # across separate ROS2 processes, Python runs, and CI restarts.
        seed = int.from_bytes(hashlib.sha256(label.encode('utf-8')).digest()[:8], 'big')
        rng = np.random.default_rng(seed)
        emb = rng.standard_normal(512)
        return emb / (np.linalg.norm(emb) + 1e-8)

    # ------------------------------------------------------------------
    # Path planning (Dijkstra)
    # ------------------------------------------------------------------

    def plan(self, start_id: int,
             goal_id: int) -> tuple[list[int], float]:
        """
        Dijkstra over the semantic graph.
        Returns (path_as_node_ids, total_cost).
        Ignores impassable edges.
        """
        import heapq

        if start_id not in self.nodes or goal_id not in self.nodes:
            raise ValueError(f"Node {start_id} or {goal_id} not in map")

        dist = {nid: np.inf for nid in self.nodes}
        prev: dict[int, Optional[int]] = {nid: None for nid in self.nodes}
        dist[start_id] = 0.0
        heap = [(0.0, start_id)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for edge in self._adj.get(u, []):
                if not edge.passable:
                    continue
                alt = dist[u] + edge.weight
                if alt < dist[edge.dst]:
                    dist[edge.dst] = alt
                    prev[edge.dst] = u
                    heapq.heappush(heap, (alt, edge.dst))

        if np.isinf(dist[goal_id]):
            logger.warning("No path from %d to %d", start_id, goal_id)
            return [], np.inf

        path, cur = [], goal_id
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path, dist[goal_id]

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "label": n.label,
                    "centroid": n.centroid_xy,
                    "properties": n.properties,
                    "embedding": n.embedding.tolist() if n.embedding is not None else None,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {
                    "src": e.src, "dst": e.dst,
                    "weight": e.weight, "passable": e.passable,
                    "type": e.transition_type,
                }
                for e in self.edges
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TopologicalSemanticMap":
        m = cls()
        ids = set()
        for n in data["nodes"]:
            nid = n["id"]
            if not isinstance(nid, int) or nid < 0 or nid in ids:
                raise ValueError("Invalid or duplicate semantic node ID")
            ids.add(nid)
            coords = tuple(n["centroid"])
            if len(coords) != 2 or not all(math.isfinite(float(v)) for v in coords):
                raise ValueError("Invalid semantic node centroid")
            saved = n.get("embedding")
            embedding = None if saved is None else np.asarray(saved, dtype=float)
            if embedding is not None and (embedding.ndim != 1 or not np.isfinite(embedding).all()):
                raise ValueError("Invalid serialized semantic embedding")
            m.nodes[nid] = SemanticNode(nid, n["label"], coords, embedding,
                                        n.get("properties", {}))
            m._adj[nid] = []
        m._next_id = max(ids, default=-1) + 1
        for e in data["edges"]:
            src,dst = e["src"],e["dst"]
            weight = float(e["weight"])
            if src not in ids or dst not in ids:
                raise ValueError("Semantic graph edge references nonexistent node")
            if not math.isfinite(weight) or weight < 0:
                raise ValueError("Invalid serialized traversal cost")
            edge = SemanticEdge(src,dst,weight,bool(e["passable"]),e["type"])
            m.edges.append(edge)
            m._adj[src].append(edge)
        return m

    def summary(self) -> str:
        return (
            f"TopologicalSemanticMap | "
            f"{len(self.nodes)} nodes | "
            f"{len(self.edges)} edges | "
            f"{sum(1 for e in self.edges if not e.passable)} blocked"
        )
