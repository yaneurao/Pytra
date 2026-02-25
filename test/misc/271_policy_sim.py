from __future__ import annotations

from dataclasses import dataclass
from typing import List
import random
import statistics

SCRIPT_ID = 271
TOPIC = ""policy_sim""
SEED = 1910


@dataclass
class Transaction:
    day: int
    amount: float


def roll(seed: int) -> List[Transaction]:
    rng = random.Random(seed)
    out: List[Transaction] = []
    bal = 1000.0
    for day in range(30):
        delta = rng.randint(-120, 140)
        bal += delta
        if bal < 0:
            bal = rng.randint(0, 50)
        out.append(Transaction(day, bal))
    return out


def windows(values: List[float], size: int) -> List[float]:
    out = []
    for i in range(len(values) - size + 1):
        window = values[i:i + size]
        out.append(sum(window) / size)
    return out


def drawdown(values: List[float]) -> float:
    peak = values[0]
    worst = 0.0
    for v in values:
        if v > peak:
            peak = v
        worst = min(worst, v - peak)
    return worst


def summary(trx: List[Transaction]) -> None:
    values = [t.amount for t in trx]
    print(f"{TOPIC} id={SCRIPT_ID}")
    print(f"samples={len(values)} mean={statistics.mean(values):.2f} median={statistics.median(values):.2f}")
    print(f"min={min(values):.2f} max={max(values):.2f} drawdown={drawdown(values):.2f}")
    print(f"ma3_last={windows(values, 3)[-1]:.2f}")


def momentum(values: List[float]) -> List[float]:
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    return deltas


def main() -> None:
    tx = roll(SEED)
    summary(tx)
    moms = momentum([t.amount for t in tx])
    print("sign", [1 if d > 0 else -1 for d in moms[:8]])


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
