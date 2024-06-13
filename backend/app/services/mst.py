import datetime
from typing import List, Dict, Optional
from backend.app.db_config.models import Route, Trip, StopTime

class DisjointSet:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, u):
        if self.parent[u] != u:
            self.parent[u] = self.find(self.parent[u])
        return self.parent[u]

    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        if self.rank[root_u] < self.rank[root_v]:
            self.parent[root_u] = root_v
        elif self.rank[root_u] > self.rank[root_v]:
            self.parent[root_v] = root_u
        else:
            self.parent[root_v] = root_u
            self.rank[root_u] += 1

async def kruskal(graph: Dict, date: datetime.date):
    """Computes the minimum spanning tree of the metro network using Kruskal's algorithm.

    Args:
        graph: The weighted graph representing the metro network.
        date: The date for which to compute the MST.

    Returns:
        A list of edges in the MST, sorted by weight (travel time).
    """

    edges = []
    for stop1 in graph:
        for stop2, weight in graph[stop1].items():
            edges.append((weight, stop1, stop2))
    edges.sort()

    num_stops = len(graph)
    disjoint_set = DisjointSet(num_stops)
    mst = []
    total_weight = 0

    for weight, stop1, stop2 in edges:
        if disjoint_set.find(stop1) != disjoint_set.find(stop2):
            disjoint_set.union(stop1, stop2)
            mst.append((stop1, stop2, weight))
            total_weight += weight

    return mst, total_weight