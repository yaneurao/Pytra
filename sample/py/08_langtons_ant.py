# 08: ラングトンのアリの軌跡をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    i = 0
    y = 0
    while y < h:
        x = 0
        while x < w:
            frame[i] = 255 if grid[y][x] else 0
            i += 1
            x += 1
        y += 1
    return bytes(frame)


def run_08_langtons_ant() -> None:
    w = 240
    h = 240
    out_path = "sample/out/08_langtons_ant.gif"

    start = perf_counter()

    grid: list[list[int]] = []
    gy = 0
    while gy < h:
        row: list[int] = []
        gx = 0
        while gx < w:
            row.append(0)
            gx += 1
        grid.append(row)
        gy += 1
    x = w // 2
    y = h // 2
    d = 0

    steps_total = 180000
    capture_every = 3000
    frames: list[bytes] = []

    i = 0
    while i < steps_total:
        if grid[y][x] == 0:
            d = (d + 1) % 4
            grid[y][x] = 1
        else:
            d = (d + 3) % 4
            grid[y][x] = 0

        if d == 0:
            y = (y - 1 + h) % h
        elif d == 1:
            x = (x + 1) % w
        elif d == 2:
            y = (y + 1) % h
        else:
            x = (x - 1 + w) % w

        if i % capture_every == 0:
            frames.append(capture(grid, w, h))
        i += 1

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_08_langtons_ant()
