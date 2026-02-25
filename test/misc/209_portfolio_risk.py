from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
import math

SCRIPT_ID = 209
TOPIC = ""portfolio_risk""
SEED = 1476


@dataclass
class Point:
    x: float
    y: float

    def norm(self) -> float:
        return math.hypot(self.x, self.y)


def build_spiral(n: int) -> List[Point]:
    out = []
    for i in range(n):
        a = i * 0.2
        out.append(Point(math.cos(a) * i * 0.25, math.sin(a) * i * 0.25))
    return out


def polar_to_bbox(points: List[Point]) -> Tuple[float, float, float, float]:
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def path_length(points: List[Point]) -> float:
    total = 0.0
    for i in range(1, len(points)):
        dx = points[i].x - points[i - 1].x
        dy = points[i].y - points[i - 1].y
        total += math.hypot(dx, dy)
    return total


def extremes(points: List[Point]) -> List[Point]:
    mx = max(points, key=lambda p: p.norm())
    mn = min(points, key=lambda p: p.norm())
    return [mn, mx]


def classify(points: List[Point], threshold: float) -> dict[str, int]:
    buckets = {"near": 0, "far": 0}
    for p in points:
        buckets["near" if p.norm() < threshold else "far"] += 1
    return buckets


def main() -> None:
    pts = build_spiral(80 + SEED % 30)
    box = polar_to_bbox(pts)
    extremes_pair = extremes(pts)
    counts = classify(pts, threshold=(SEED % 7) + 10)
    print(f"{TOPIC} id={SCRIPT_ID} len={len(pts)}")
    print(f"bbox={tuple(round(v, 2) for v in box)}")
    print(f"path={path_length(pts):.2f}")
    print(f"min={extremes_pair[0]} max={extremes_pair[1]}")
    print(f"split={counts}")


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
