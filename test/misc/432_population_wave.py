from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
import random

SCRIPT_ID = 432
TOPIC = ""population_wave""
SEED = 3037


@dataclass
class Trade:
    ticker: str
    qty: int
    px: float


def sample_trades(seed: int) -> List[Trade]:
    rng = random.Random(seed)
    out: List[Trade] = []
    for t in ["A", "B", "C", "D", "E"]:
        for i in range(8):
            out.append(Trade(t, (rng.randint(1, 10) * ((seed % 4) + 1)), rng.uniform(90, 110)))
    return out


def pnl(trades: List[Trade]) -> Dict[str, float]:
    total = 0.0
    per: Dict[str, float] = {}
    for t in trades:
        value = t.qty * t.px
        per[t.ticker] = per.get(t.ticker, 0.0) + value
        total += value
    return {"total": total, **per}


def ranked(per: Dict[str, float]) -> List[str]:
    return sorted(per.keys(), key=lambda k: per[k], reverse=True)


def shock(trades: List[Trade]) -> float:
    max_v = max(t.qty * t.px for t in trades)
    min_v = min(t.qty * t.px for t in trades)
    return max_v - min_v


def main() -> None:
    trades = sample_trades(SEED)
    p = pnl(trades)
    print(f"{TOPIC}:{SCRIPT_ID} positions={len(trades)}")
    print("tickers", ranked(p))
    print("total", round(p["total"], 2))
    print("range", round(shock(trades), 2))


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
