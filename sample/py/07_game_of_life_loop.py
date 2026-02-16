# 07: Game of Life の進化をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def next_state(grid: list[list[int]], w: int, h: int) -> list[list[int]]:
    nxt: list[list[int]] = []
    y = 0
    while y < h:
        row: list[int] = []
        x = 0
        while x < w:
            cnt = 0
            dy = -1
            while dy <= 1:
                dx = -1
                while dx <= 1:
                    if dx != 0 or dy != 0:
                        nx = (x + dx + w) % w
                        ny = (y + dy + h) % h
                        cnt += grid[ny][nx]
                    dx += 1
                dy += 1
            alive = grid[y][x]
            if alive == 1 and (cnt == 2 or cnt == 3):
                row.append(1)
            elif alive == 0 and cnt == 3:
                row.append(1)
            else:
                row.append(0)
            x += 1
        nxt.append(row)
        y += 1
    return nxt


def render(grid: list[list[int]], w: int, h: int, cell: int) -> bytes:
    width = w * cell
    height = h * cell
    frame = bytearray(width * height)
    y = 0
    while y < h:
        x = 0
        while x < w:
            v = 255 if grid[y][x] else 0
            yy = 0
            while yy < cell:
                base = (y * cell + yy) * width + x * cell
                xx = 0
                while xx < cell:
                    frame[base + xx] = v
                    xx += 1
                yy += 1
            x += 1
        y += 1
    return bytes(frame)


def run_07_game_of_life_loop() -> None:
    w = 96
    h = 72
    cell = 3
    steps = 70
    out_path = "sample/out/07_game_of_life_loop.gif"

    start = perf_counter()
    grid: list[list[int]] = []
    y = 0
    while y < h:
        row: list[int] = []
        x = 0
        while x < w:
            row.append(1 if ((x * 17 + y * 31 + 13) % 11) < 3 else 0)
            x += 1
        grid.append(row)
        y += 1

    frames: list[bytes] = []
    i = 0
    while i < steps:
        frames.append(render(grid, w, h, cell))
        grid = next_state(grid, w, h)
        i += 1

    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_07_game_of_life_loop()
