"""Adjacency-set graph with topological sort."""
from __future__ import annotations

from collections import deque


class DiGraph:
    def __init__(self) -> None:
        self._adj: dict[str, set[str]] = {}

    def add_edge(self, src: str, dst: str) -> None:
        self._adj.setdefault(src, set()).add(dst)
        self._adj.setdefault(dst, set())

    def successors(self, node: str) -> frozenset[str]:
        return frozenset(self._adj.get(node, ()))

    def topo_order(self) -> list[str]:
        indegree = {node: 0 for node in self._adj}
        for src in self._adj:
            for dst in self._adj[src]:
                indegree[dst] += 1
        ready = deque(sorted(n for n, d in indegree.items() if d == 0))
        order: list[str] = []
        while ready:
            node = ready.popleft()
            order.append(node)
            for dst in sorted(self._adj[node]):
                indegree[dst] -= 1
                if indegree[dst] == 0:
                    ready.append(dst)
        if len(order) != len(self._adj):
            raise ValueError("graph contains a cycle")
        return order
