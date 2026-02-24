from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev
from typing import List, Dict, Tuple


FILE_ID = 51
SCENARIO = "oceanic_timeseries"
SEED = 940


@dataclass
class Tick:
    index: int
    value: float


def build_ticks(seed: int, length: int = 36) -> List[Tick]:
    out = []
    for i in range(length):
        wave = ((i * (seed % 7 + 1)) % 13) / 3
        drift = (seed % 11) * 0.7
        noise = ((i % 5) - 2) * 0.4
        down = (i // 6) * 0.25
        value = round(18 + drift + wave + noise - down + (i % 3) * 0.8, 3)
        out.append(Tick(i + 1, value))
    return out


def moving_average(values: List[float], window: int) -> List[float]:
    out: List[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        segment = values[start:i + 1]
        out.append(sum(segment) / len(segment))
    return out


def pair_deltas(values: List[float]) -> List[float]:
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def detect_turns(deltas: List[float]) -> List[int]:
    turns = []
    for i in range(1, len(deltas)):
        if (deltas[i - 1] < 0 <= deltas[i]) or (deltas[i - 1] > 0 >= deltas[i]):
            turns.append(i)
    return turns


def bucket(values: List[float], bins: int = 5) -> Dict[str, int]:
    min_v = min(values)
    max_v = max(values)
    step = (max_v - min_v) / bins
    out: Dict[str, int] = {f"bin_{i}": 0 for i in range(bins)}
    for v in values:
        idx = bins - 1 if step == 0 else min(bins - 1, int((v - min_v) / step))
        out[f"bin_{idx}"] += 1
    return out


def summarize(values: List[float]) -> Dict[str, float]:
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "avg": mean(values),
        "sd": pstdev(values) if len(values) > 1 else 0.0,
    }


class SignalLab:
    def __init__(self, ticks: List[Tick]):
        self.ticks = ticks
        self.values = [tick.value for tick in ticks]

    def smoothed(self) -> List[float]:
        return moving_average(self.values, 5)

    def extrema(self) -> Tuple[int, int]:
        min_i = min(range(len(self.values)), key=lambda i: self.values[i])
        max_i = max(range(len(self.values)), key=lambda i: self.values[i])
        return min_i + 1, max_i + 1

    def anomaly_candidates(self, z: float = 1.8) -> List[int]:
        s = self.smoothed()
        base = summarize(s)["avg"]
        spread = max(1e-6, summarize(s)["sd"])
        return [i + 1 for i, v in enumerate(s) if abs(v - base) > z * spread]

    def report(self) -> str:
        deltas = pair_deltas(self.values)
        turns = detect_turns(deltas)
        return " ".join([
            f"scenario={SCENARIO}",
            f"id={FILE_ID}",
            f"turns={len(turns)}",
            f"extrema={self.extrema()}",
            f"anomalies={self.anomaly_candidates()}",
            f"buckets={bucket(self.values)}",
        ])


def ascii_plot(values: List[float]) -> List[str]:
    levels = " ▁▂▃▄▅▆▇█"
    min_v = min(values)
    max_v = max(values)
    scale = (max_v - min_v) or 1
    out = []
    for v in values:
        idx = int((v - min_v) / scale * (len(levels) - 1))
        out.append(levels[idx])
    return out


def main() -> None:
    ticks = build_ticks(SEED)
    analyzer = SignalLab(ticks)
    print(analyzer.report())
    print("smooth=" + ",".join(f"{v:.2f}" for v in analyzer.smoothed()[:8]))
    print("summary=" + str(summarize(analyzer.values)))
    print("plot=" + "".join(ascii_plot(analyzer.values)))


if __name__ == "__main__":
    main()
