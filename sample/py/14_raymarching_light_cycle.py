# 14: 簡易レイマーチ風の光源移動シーンをGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from pylib.tra.gif import save_gif


def palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = min(255, int(20 + i * 0.9))
        g = min(255, int(10 + i * 0.7))
        b = min(255, int(30 + i))
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def scene(x: float, y: float, light_x: float, light_y: float) -> int:
    x1 = x + 0.45
    y1 = y + 0.2
    x2 = x - 0.35
    y2 = y - 0.15
    r1 = math.sqrt(x1 * x1 + y1 * y1)
    r2 = math.sqrt(x2 * x2 + y2 * y2)
    blob = math.exp(-7.0 * r1 * r1) + math.exp(-8.0 * r2 * r2)

    lx = x - light_x
    ly = y - light_y
    l = math.sqrt(lx * lx + ly * ly)
    lit = 1.0 / (1.0 + 3.5 * l * l)

    v = int(255.0 * blob * lit * 5.0)
    return min(255, max(0, v))


def run_14_raymarching_light_cycle() -> None:
    w = 320
    h = 240
    frames_n = 84
    out_path = "sample/out/14_raymarching_light_cycle.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)
        a = (t / frames_n) * math.pi * 2.0
        light_x = 0.75 * math.cos(a)
        light_y = 0.55 * math.sin(a * 1.2)

        i = 0
        for y in range(h):
            py = (y / (h - 1)) * 2.0 - 1.0
            for x in range(w):
                px = (x / (w - 1)) * 2.0 - 1.0
                frame[i] = scene(px, py, light_x, light_y)
                i += 1

        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_14_raymarching_light_cycle()
