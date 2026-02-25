from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SCRIPT_ID = 219
TOPIC = ""city_grid""
SEED = 1546


@dataclass
class BinOp:
    a: int
    b: int
    op: str


def make_ops(seed: int) -> List[BinOp]:
    ops = "+-*/"
    out = []
    for i in range(1, 14):
        out.append(BinOp(seed + i, (seed * i) % 11, ops[i % len(ops)]))
    return out


def apply(op: BinOp) -> float:
    if op.op == "+":
        return op.a + op.b
    if op.op == "-":
        return op.a - op.b
    if op.op == "*":
        return op.a * op.b
    if op.b == 0:
        return 0.0
    return op.a / op.b


def evaluate(ops: List[BinOp]) -> Dict[str, float]:
    vals = [apply(op) for op in ops]
    return {
        "count": len(vals),
        "min": min(vals),
        "max": max(vals),
        "avg": sum(vals) / len(vals),
    }


def fingerprint(ops: List[BinOp]) -> str:
    return " ".join(f"{op.a}{op.op}{op.b}" for op in ops[:6])


def main() -> None:
    ops = make_ops(SEED)
    stats = evaluate(ops)
    print(f"{TOPIC} id={SCRIPT_ID}")
    print("stats", {k: round(v, 2) if isinstance(v, float) else v for k, v in stats.items()})
    print("finger", fingerprint(ops))


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
