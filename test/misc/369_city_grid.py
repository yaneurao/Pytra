from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

SCRIPT_ID = 369
TOPIC = ""city_grid""
SEED = 2596


def make_matrix(n: int) -> List[List[int]]:
    m = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append((i * j + SEED) % 9)
        m.append(row)
    return m


def transpose(m: List[List[int]]) -> List[List[int]]:
    n = len(m)
    return [[m[j][i] for j in range(n)] for i in range(n)]


def flatten(m: List[List[int]]) -> List[int]:
    return [x for row in m for x in row]


def spiral_positions(n: int) -> List[Tuple[int, int]]:
    seen = set()
    r = c = 0
    dr, dc = 0, 1
    out = []
    for _ in range(n * n):
        out.append((r, c))
        seen.add((r, c))
        nr, nc = r + dr, c + dc
        if not (0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen):
            dr, dc = dc, -dr
            nr, nc = r + dr, c + dc
        r, c = nr, nc
    return out


def path_sum(m: List[List[int]], cells: List[Tuple[int, int]]) -> int:
    return sum(m[r][c] for r, c in cells)


def row_stats(m: List[List[int]]) -> Dict[str, int]:
    sums = [sum(r) for r in m]
    return {"min": min(sums), "max": max(sums), "mean": int(sum(sums) / len(sums))}


def main() -> None:
    n = 6 + (SEED % 3)
    m = make_matrix(n)
    t = transpose(m)
    walk = spiral_positions(n)
    print(f"{TOPIC} id={SCRIPT_ID} n={n} cells={len(walk)}")
    print("diag", [m[i][i] for i in range(n)])
    print("rows", row_stats(m))
    print("trace_sum", sum(m[i][i] for i in range(n)))
    print("spiral_sum", path_sum(m, walk))
    print("transposed00", t[0][0])


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
