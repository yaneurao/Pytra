# 08: Sample that outputs Langton's Ant trajectories as a GIF.

from __future__ import annotations

from time import perf_counter

from pytra.runtime.gif import grayscale_palette, save_gif


def capture(grid: list[list[int]], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    for y in range(h):
        row_base = y * w
        for x in range(w):
            frame[row_base + x] = 255 if grid[y][x] else 0
    return bytes(frame)


def run_08_langtons_ant() -> None:
    w = 420
    h = 420
    out_path = "sample/out/08_langtons_ant.gif"

    start = perf_counter()

    grid: list[list[int]] = [[0] * w for _ in range(h)]
    x = w // 2
    y = h // 2
    d = 0

    steps_total = 600000
    capture_every = 3000
    frames: list[bytes] = []

    for i in range(steps_total):
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

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_08_langtons_ant()
