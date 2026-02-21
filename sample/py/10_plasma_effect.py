# 10: Sample that outputs a plasma effect as a GIF.

from __future__ import annotations

import math
from time import perf_counter

from pytra.runtime.gif import grayscale_palette, save_gif


def run_10_plasma_effect() -> None:
    w = 320
    h = 240
    frames_n = 216
    out_path = "sample/out/10_plasma_effect.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)
        for y in range(h):
            row_base = y * w
            for x in range(w):
                dx = x - 160
                dy = y - 120
                v = (
                    math.sin((x + t * 2.0) * 0.045)
                    + math.sin((y - t * 1.2) * 0.05)
                    + math.sin((x + y + t * 1.7) * 0.03)
                    + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18)
                )
                c = int((v + 4.0) * (255.0 / 8.0))
                if c < 0:
                    c = 0
                if c > 255:
                    c = 255
                frame[row_base + x] = c
        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_10_plasma_effect()
