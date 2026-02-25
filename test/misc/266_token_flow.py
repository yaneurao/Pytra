from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SCRIPT_ID = 266
TOPIC = ""token_flow""
SEED = 1875


@dataclass
class Rule:
    name: str
    active: bool


def build_rules(seed: int) -> List[Rule]:
    out = []
    for i in range(12):
        out.append(Rule(f"r{i}", ((seed + i) % 2) == 0))
    return out


def enabled_count(rules: List[Rule]) -> int:
    return sum(1 for r in rules if r.active)


def evaluate(rules: List[Rule]) -> Dict[str, int]:
    on = [r.name for r in rules if r.active]
    return {"active": len(on), "inactive": len(rules) - len(on)}


def route(active: int, total: int) -> List[str]:
    out = []
    for i in range(total):
        out.append("ALLOW" if (i < active or total - i <= active) else "BLOCK")
    return out


def main() -> None:
    rules = build_rules(SEED)
    score = evaluate(rules)
    orders = route(score["active"], len(rules))
    print(f"{TOPIC}:{SCRIPT_ID} total={len(rules)} active={score['active']}")
    print("sample", orders[:8])
    print("flags", [r.name for r in rules if r.active][:6])


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
