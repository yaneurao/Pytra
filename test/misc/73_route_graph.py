from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


FILE_ID = 73
SCENARIO = "route_graph"
SEED = 1314


@dataclass
class Arc:
    src: str
    dst: str
    cost: int


def make_nodes(seed: int) -> List[str]:
    base = ["ingest", "parse", "score", "alert", "ship"]
    if seed % 2 == 0:
        base.append("archive")
    if seed % 3 == 0:
        base.append("review")
    return base


def make_arcs(nodes: List[str]) -> List[Arc]:
    out = []
    for i, src in enumerate(nodes):
        for j in range(1, min(3, len(nodes) - i)):
            dst = nodes[(i + j) % len(nodes)]
            if src != dst:
                out.append(Arc(src, dst, (i + j + 1)))
    out.append(Arc(nodes[-1], nodes[0], 1))
    return out


def build_graph(arcs: List[Arc]) -> Dict[str, List[Tuple[str, int]]]:
    graph = defaultdict(list)
    indeg: Dict[str, int] = defaultdict(int)
    for arc in arcs:
        graph[arc.src].append((arc.dst, arc.cost))
        indeg[arc.dst] += 1
        if arc.src not in indeg:
            indeg[arc.src] = 0
    return graph, indeg


def bfs_order(graph: Dict[str, List[Tuple[str, int]]], start: str) -> List[str]:
    q = deque([start])
    seen = {start}
    order = []
    while q:
        cur = q.popleft()
        order.append(cur)
        for nxt, _ in graph.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return order


def dijkstra(graph: Dict[str, List[Tuple[str, int]]], start: str) -> Dict[str, int]:
    dist = {start: 0}
    unvisited = set(graph.keys())
    while unvisited:
        cur = None
        cur_d = None
        for node in unvisited:
            d = dist.get(node)
            if d is not None and (cur_d is None or d < cur_d):
                cur, cur_d = node, d
        if cur is None:
            break
        unvisited.remove(cur)
        for nxt, cost in graph.get(cur, []):
            nd = dist[cur] + cost
            if nd < dist.get(nxt, 10**9):
                dist[nxt] = nd
    return dist


def reachable_subgraph(graph: Dict[str, List[Tuple[str, int]]], start: str) -> List[str]:
    return bfs_order(graph, start)


def longest_step(graph: Dict[str, List[Tuple[str, int]]]) -> Tuple[str, str, int]:
    heavy = max((src, dst, cost) for src, edges in graph.items() for dst, cost in edges)
    return heavy


def print_arc_table(arcs: List[Arc]) -> None:
    for arc in arcs:
        print(f"{arc.src}->{arc.dst}:{arc.cost}")


def main() -> None:
    nodes = make_nodes(SEED)
    arcs = make_arcs(nodes)
    graph, indeg = build_graph(arcs)
    start = nodes[0]
    print(f"id={FILE_ID} scenario={SCENARIO}")
    print(f"nodes={nodes}")
    print(f"indeg={dict(sorted(indeg.items()))}")
    print(f"bfs={reachable_subgraph(graph, start)}")
    print(f"dist={dijkstra(graph, start)}")
    print(f"heavy_edge={longest_step(graph)}")
    print("table=")
    print_arc_table(arcs)


if __name__ == "__main__":
    main()
