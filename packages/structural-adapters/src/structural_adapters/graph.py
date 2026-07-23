"""Composition reachability over a directed, confidence-weighted graph.

Port of the prototype bridge's ``CategoryGraph.reachable_from`` — the actual
"composition oracle" behind structural triage. A target is reachable iff a
composable spine of edges connects some source to it within ``max_length``
hops; the returned weight is the best multiplicative confidence over any such
spine (all-unit-weight graphs yield 1.0). Deterministic: the best-weight map
is independent of traversal order.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    confidence: float = 1.0
    provenance: str = ""


class CompositionIndex:
    """Minimal category-graph surface the audit procedures require."""

    def __init__(self) -> None:
        self._objects: set[str] = set()
        self._edges: list[Edge] = []

    def add_object(self, name: str) -> None:
        self._objects.add(name)

    def add_edge(self, edge: Edge) -> None:
        self._objects.add(edge.source)
        self._objects.add(edge.target)
        self._edges.append(edge)

    def has_object(self, name: str) -> bool:
        return name in self._objects

    def edges(self) -> list[Edge]:
        return list(self._edges)

    def reachable_from(self, sources: set[str],
                       max_length: int = 10) -> dict[str, float]:
        """Nodes reachable from ``sources`` with their best enriched weight."""
        adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for edge in self._edges:
            adjacency[edge.source].append((edge.target, edge.confidence))

        best: dict[str, float] = {}
        queue: deque[tuple[str, float, int]] = deque()
        for source in sources:
            if source in self._objects:
                best[source] = 1.0
                queue.append((source, 1.0, 0))
        while queue:
            node, weight, depth = queue.popleft()
            if depth >= max_length:
                continue
            for target, confidence in adjacency.get(node, ()):
                new_weight = weight * confidence
                if new_weight > best.get(target, -1.0):
                    best[target] = new_weight
                    queue.append((target, new_weight, depth + 1))
        return best

    def path_count(self, source: str, target: str, max_length: int = 2) -> int:
        """Number of distinct directed paths source -> target within max_length.

        Replaces the prototype's ``native_paths(...)`` length queries (used
        only as evidence counts in twin findings).
        """
        adjacency: dict[str, list[str]] = defaultdict(list)
        for edge in self._edges:
            adjacency[edge.source].append(edge.target)

        count = 0
        frontier: deque[tuple[str, int]] = deque([(source, 0)])
        while frontier:
            node, depth = frontier.popleft()
            if depth > 0 and node == target:
                count += 1
                continue
            if depth >= max_length:
                continue
            for nxt in adjacency.get(node, ()):
                frontier.append((nxt, depth + 1))
        return count
