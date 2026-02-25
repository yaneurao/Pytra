from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple

SCRIPT_ID = 306
TOPIC = ""log_trace""
SEED = 2155


graph: Dict[str, List[str]] = {}
for i in range(12):
    node = f"N{i}"
    graph[node] = [f"N{(i + 1 + (SEED + i) % 4) % 12}", f"N{(i + 3 + SEED % 5) % 12}"]


def bfs(start: str) -> Dict[str, int]:
    dist = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nxt in graph[cur]:
            if nxt not in dist:
                dist[nxt] = dist[cur] + 1
                q.append(nxt)
    return dist


def components() -> List[Tuple[str, int]]:
    seen = set()
    comp = []
    for s in graph:
        if s in seen:
            continue
        dist = bfs(s)
        seen.update(dist)
        comp.append((s, len(dist)))
    return comp


def centrality() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for start in graph:
        out[start] = len(bfs(start))
    return out


def bridges() -> List[Tuple[str, str]]:
    all_edges = []
    for s, outs in graph.items():
        all_edges.extend((s, t) for t in outs)
    return all_edges[: min(5, len(all_edges))]


def main() -> None:
    print(f"{TOPIC} id={SCRIPT_ID} nodes={len(graph)}")
    print("components", components())
    print("central", sorted(centrality().items(), key=lambda x: x[1], reverse=True)[:4])
    print("sample_edges", bridges())


if __name__ == "__main__":
    main()



def _probe_sequence(seed: int, count: int = 18) -> list[int]:
    out: list[int] = []
    x = seed
    for _ in range(count):
        x = (x * 31 + 7) % 97
        out.append(x)
    return out


def _running_sum(values: list[float]) -> list[float]:
    total = 0.0
    out: list[float] = []
    for value in values:
        total += value
        out.append(total)
    return out


def _histogram(values: list[float], bins: int = 5) -> dict[str, int]:
    if not values:
        return {}
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return {"constant": len(values)}
    width = (hi - lo) / bins
    out: dict[str, int] = {}
    for value in values:
        idx = int((value - lo) / width)
        if idx == bins:
            idx = bins - 1
        out[f"b{idx}"] = out.get(f"b{idx}", 0) + 1
    return out


def _debug_tail() -> None:
    probe = _probe_sequence(SCRIPT_ID)
    series = [((n % 11) / 7.0) for n in probe]
    rs = _running_sum(series)
    print("extra_probe", probe)
    print("extra_bins", _histogram(series))
    print("extra_running", [round(v, 2) for v in rs])


if __name__ == "__main__":
    _debug_tail()
