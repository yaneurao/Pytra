from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

SCRIPT_ID = 349
TOPIC = ""resource_pool""
SEED = 2456


def build_points(seed: int) -> List[Tuple[int, int]]:
    pts: List[Tuple[int, int]] = []
    for i in range(20):
        x = (seed * (i + 2)) % 17
        y = ((seed + i) ** 2) % 19
        pts.append((x, y))
    return pts


def slope(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    dx = b[0] - a[0]
    if dx == 0:
        return float('inf')
    return (b[1] - a[1]) / dx


def segments(points: List[Tuple[int, int]]) -> List[float]:
    out: List[float] = []
    for i in range(1, len(points)):
        out.append(round(slope(points[i - 1], points[i]), 2))
    return out


def moving(points: List[Tuple[int, int]], k: int = 3) -> List[float]:
    deltas = segments(points)
    out = []
    for i in range(len(deltas)):
        start = max(0, i - k + 1)
        out.append(sum(deltas[start : i + 1]) / (i - start + 1))
    return out


def main() -> None:
    pts = build_points(SEED)
    slopes = segments(pts)
    ma = moving(slopes)
    print(f"{TOPIC} id={SCRIPT_ID} n={len(pts)}")
    print("slopes_head", slopes[:10])
    print("moving_head", [round(v, 2) for v in ma[:10]])
    infs = sum(1 for v in slopes if v == float('inf'))
    print("vertical", infs)


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
