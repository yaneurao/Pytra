from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

SCRIPT_ID = 491
TOPIC = ""token_flow""
SEED = 3450


@dataclass
class Cell:
    x: int
    y: int
    alive: bool


def make_grid(seed: int, n: int = 8) -> List[List[Cell]]:
    out = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(Cell(i, j, ((i * j + seed) % 3) == 0))
        out.append(row)
    return out


def neighbors(grid: List[List[Cell]], x: int, y: int) -> int:
    n = len(grid)
    cnt = 0
    for i in range(max(0, x - 1), min(n, x + 2)):
        for j in range(max(0, y - 1), min(n, y + 2)):
            if (i, j) != (x, y) and grid[i][j].alive:
                cnt += 1
    return cnt


def step(grid: List[List[Cell]]) -> List[List[Cell]]:
    n = len(grid)
    out = [[Cell(i, j, False) for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            a = neighbors(grid, i, j)
            cur = grid[i][j].alive
            out[i][j].alive = (a == 3) or (cur and a == 2)
    return out


def count_alive(grid: List[List[Cell]]) -> int:
    return sum(cell.alive for row in grid for cell in row)


def signature(grid: List[List[Cell]]) -> str:
    return "".join("1" if c.alive else "0" for row in grid for c in row)


def main() -> None:
    g = make_grid(SEED)
    history = []
    for _ in range(8):
        history.append(count_alive(g))
        g = step(g)
    print(f"{TOPIC} id={SCRIPT_ID}")
    print("history", history)
    print("alive_end", count_alive(g))
    print("signature", signature(g)[:24])


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
