from __future__ import annotations

from collections import deque
from typing import Dict, List, Tuple

Grid = List[str]

MAZE = [
    "##########",
    "#S   #   #",
    "# ## # # #",
    "#    #   #",
    "#### ## ##",
    "#      #E#",
    "##########",
]


def find_char(grid: Grid, target: str) -> Tuple[int, int]:
    for r, row in enumerate(grid):
        c = row.find(target)
        if c != -1:
            return r, c
    raise ValueError(f"missing {target}")


def neighbors(pos: Tuple[int, int], grid: Grid) -> List[Tuple[int, int]]:
    r, c = pos
    deltas = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    out = []
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] != "#":
            out.append((nr, nc))
    return out


def bfs(grid: Grid, start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[Tuple[int, int], Tuple[int, int]]:
    q = deque([start])
    prev: Dict[Tuple[int, int], Tuple[int, int]] = {start: start}
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nxt in neighbors(cur, grid):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return prev


def build_path(prev: Dict[Tuple[int, int], Tuple[int, int]], goal: Tuple[int, int], start: Tuple[int, int]) -> List[Tuple[int, int]]:
    if goal not in prev:
        return []
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def overlay_path(grid: Grid, path: List[Tuple[int, int]]) -> Grid:
    rows = [list(row) for row in grid]
    for r, c in path[1:-1]:
        if rows[r][c] == " ":
            rows[r][c] = "*"
    return ["".join(row) for row in rows]


def main() -> None:
    start = find_char(MAZE, "S")
    goal = find_char(MAZE, "E")
    prev = bfs(MAZE, start, goal)
    path = build_path(prev, goal, start)
    print(f"start={start}, goal={goal}, length={len(path)}")
    for row in overlay_path(MAZE, path):
        print(row)


if __name__ == "__main__":
    main()


def _maze_stats(path: list[tuple[int, int]]) -> dict[str, int]:
    return {
        "steps": len(path),
        "row_span": max(r for r, _ in path) - min(r for r, _ in path) if path else 0,
        "col_span": max(c for _, c in path) - min(c for _, c in path) if path else 0,
    }


def _maze_demo() -> None:
    start = find_char(MAZE, "S")
    goal = find_char(MAZE, "E")
    prev = bfs(MAZE, start, goal)
    path = build_path(prev, goal, start)
    print("path", path)
    print("stats", _maze_stats(path))


if __name__ == "__main__":
    _maze_demo()
