from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SCRIPT_ID = 112
TOPIC = ""text_funnel""
SEED = 797


@dataclass
class Node:
    id: int
    deps: List[int]


def build_graph(seed: int) -> Dict[int, Node]:
    out = {}
    for i in range(1, 11):
        d = [(i + j) % 10 for j in range(1, (seed % 3) + 2)]
        out[i] = Node(i, d)
    return out


def topo(g: Dict[int, Node]) -> List[int]:
    all_nodes = set(g.keys())
    indeg = {k: 0 for k in all_nodes}
    for n in g.values():
        for d in n.deps:
            if d in indeg:
                indeg[d] += 1
    queue = [n for n, v in indeg.items() if v == 0]
    out = []
    while queue:
        cur = queue.pop(0)
        out.append(cur)
        for d in g[cur].deps:
            if d in indeg:
                indeg[d] -= 1
                if indeg[d] == 0:
                    queue.append(d)
    return out


def depth(g: Dict[int, Node], start: int, seen=None) -> int:
    if seen is None:
        seen = set()
    if start in g and start not in seen:
        seen.add(start)
        return 1 + max((depth(g, d, seen) for d in g[start].deps if d in g), default=0)
    return 0


def report(g: Dict[int, Node]) -> Dict[str, int]:
    t = topo(g)
    d = depth(g, t[0] if t else 1)
    return {"order": len(t), "depth": d}


def main() -> None:
    g = build_graph(SEED)
    rep = report(g)
    print(f"{TOPIC} id={SCRIPT_ID} nodes={len(g)}")
    print("topo", topo(g))
    print("metrics", rep)


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
