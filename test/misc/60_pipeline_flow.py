from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple


FILE_ID = 60
SCENARIO = "pipeline_flow"
SEED = 1093


@dataclass
class Step:
    name: str
    duration: int
    deps: List[str]


def build_plan(seed: int) -> List[Step]:
    core = [
        Step("fetch", 2, []),
        Step("parse", 3, ["fetch"]),
        Step("validate", 1, ["parse"]),
        Step("transform", 4, ["parse"]),
        Step("score", 2, ["validate", "transform"]),
        Step("notify", 1, ["score"]),
    ]
    if seed % 2 == 0:
        core.append(Step("compress", 2, ["score"]))
    if seed % 3 == 0:
        core.append(Step("archive", 1, ["compress" if seed % 2 == 0 else "score"]))
    return core


def to_graph(steps: List[Step]) -> Tuple[Dict[str, List[str]], Dict[str, int]]:
    out: Dict[str, List[str]] = defaultdict(list)
    indeg: Dict[str, int] = {}
    for s in steps:
        indeg[s.name] = indeg.get(s.name, 0)
        for dep in s.deps:
            out[dep].append(s.name)
            indeg[s.name] = indeg.get(s.name, 0) + 1
            out[s.name]
    return out, indeg


def topo(graph: Dict[str, List[str]], indeg: Dict[str, int]) -> List[str]:
    q = deque([name for name, d in indeg.items() if d == 0])
    out: List[str] = []
    while q:
        cur = q.popleft()
        out.append(cur)
        for nxt in graph.get(cur, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    return out


def runtime(order: List[str], mapping: Dict[str, Step]) -> Dict[str, Tuple[int, int]]:
    t = 0
    out: Dict[str, Tuple[int, int]] = {}
    for name in order:
        st = t
        ed = st + mapping[name].duration
        out[name] = (st, ed)
        t = ed
    return out


def critical(order: List[str], mapping: Dict[str, Step]) -> str:
    return max(order, key=lambda name: mapping[name].duration)


def main() -> None:
    steps = build_plan(SEED)
    mapping = {s.name: s for s in steps}
    graph, indeg = to_graph(steps)
    order = topo(graph, indeg)
    print(f"id={FILE_ID} scenario={SCENARIO}")
    print(f"order={order}")
    print(f"duration={sum(mapping[n].duration for n in order)}")
    print(f"critical={critical(order, mapping)}")
    print(f"timeline={runtime(order, mapping)}")
    if len(order) != len(steps):
        print("warning=cycle")
    else:
        print("status=ok")


if __name__ == "__main__":
    main()
