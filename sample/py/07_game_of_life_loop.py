# 07: Sample that outputs Game of Life evolution as a GIF.

from __future__ import annotations

from time import perf_counter

from pytra.runtime.gif import grayscale_palette, save_gif


def next_state(grid: list[list[int]], w: int, h: int) -> list[list[int]]:
    nxt: list[list[int]] = []
    for y in range(h):
        row: list[int] = []
        for x in range(w):
            cnt = 0
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx != 0 or dy != 0:
                        nx = (x + dx + w) % w
                        ny = (y + dy + h) % h
                        cnt += grid[ny][nx]
            alive = grid[y][x]
            if alive == 1 and (cnt == 2 or cnt == 3):
                row.append(1)
            elif alive == 0 and cnt == 3:
                row.append(1)
            else:
                row.append(0)
        nxt.append(row)
    return nxt


def render(grid: list[list[int]], w: int, h: int, cell: int) -> bytes:
    width = w * cell
    height = h * cell
    frame = bytearray(width * height)
    for y in range(h):
        for x in range(w):
            v = 255 if grid[y][x] else 0
            for yy in range(cell):
                base = (y * cell + yy) * width + x * cell
                for xx in range(cell):
                    frame[base + xx] = v
    return bytes(frame)


def run_07_game_of_life_loop() -> None:
    w = 144
    h = 108
    cell = 4
    steps = 210
    out_path = "sample/out/07_game_of_life_loop.gif"

    start = perf_counter()
    grid: list[list[int]] = [[0] * w for _ in range(h)]

    # Lay down sparse noise so the whole field is less likely to stabilize too early.
    # Avoid large integer literals so all transpilers handle the expression consistently.
    for y in range(h):
        for x in range(w):
            noise = (x * 37 + y * 73 + (x * y) % 19 + (x + y) % 11) % 97
            if noise < 3:
                grid[y][x] = 1

    # Place multiple well-known long-lived patterns.
    glider = [
        [0, 1, 0],
        [0, 0, 1],
        [1, 1, 1],
    ]
    r_pentomino = [
        [0, 1, 1],
        [1, 1, 0],
        [0, 1, 0],
    ]
    lwss = [
        [0, 1, 1, 1, 1],
        [1, 0, 0, 0, 1],
        [0, 0, 0, 0, 1],
        [1, 0, 0, 1, 0],
    ]

    for gy in range(8, h - 8, 18):
        for gx in range(8, w - 8, 22):
            kind = (gx * 7 + gy * 11) % 3
            if kind == 0:
                ph = len(glider)
                for py in range(ph):
                    pw = len(glider[py])
                    for px in range(pw):
                        if glider[py][px] == 1:
                            grid[(gy + py) % h][(gx + px) % w] = 1
            elif kind == 1:
                ph = len(r_pentomino)
                for py in range(ph):
                    pw = len(r_pentomino[py])
                    for px in range(pw):
                        if r_pentomino[py][px] == 1:
                            grid[(gy + py) % h][(gx + px) % w] = 1
            else:
                ph = len(lwss)
                for py in range(ph):
                    pw = len(lwss[py])
                    for px in range(pw):
                        if lwss[py][px] == 1:
                            grid[(gy + py) % h][(gx + px) % w] = 1

    frames: list[bytes] = []
    for _ in range(steps):
        frames.append(render(grid, w, h, cell))
        grid = next_state(grid, w, h)

    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_07_game_of_life_loop()
