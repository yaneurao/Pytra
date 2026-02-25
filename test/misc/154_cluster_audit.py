from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SCRIPT_ID = 154
TOPIC = ""cluster_audit""
SEED = 1091


@dataclass
class Step:
    name: str
    cost: int


def make_steps(seed: int) -> List[Step]:
    out: List[Step] = []
    names = ["ingest", "clean", "transform", "validate", "publish", "archive"]
    for idx, name in enumerate(names):
        out.append(Step(f"{name}_{seed % 11}", ((seed + idx * 3) % 7) + 1))
    return out


def expand_plan(steps: List[Step], rounds: int) -> List[Step]:
    out = []
    for _ in range(rounds):
        for s in steps:
            if (s.cost + _ + SEED) % 2:
                out.append(Step(s.name + f"_{_}", s.cost + 1))
    return out


def accumulate(steps: List[Step]) -> Dict[str, int]:
    total = 0
    byname: Dict[str, int] = {}
    for s in steps:
        total += s.cost
        byname[s.name] = byname.get(s.name, 0) + s.cost
    byname["total"] = total
    return byname


def critical_path(steps: List[Step]) -> int:
    return sum(step.cost for step in steps)


def main() -> None:
    base = make_steps(SEED)
    plan = expand_plan(base, 4)
    stats = accumulate(plan)
    print(f"{TOPIC} id={SCRIPT_ID} count={len(plan)} total={stats['total']}")
    print("crit", critical_path(plan))
    top = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    print("top", top[:4])


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
