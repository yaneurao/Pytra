# 15: Sample that renders wave interference animation and writes a GIF.

from __future__ import annotations

import math
from time import perf_counter

from pytra.utils.gif import grayscale_palette, save_gif


def run_15_wave_interference_loop() -> None:
    w = 320
    h = 240
    frames_n = 96
    out_path = "sample/out/15_wave_interference_loop.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)
        phase = t * 0.12
        for y in range(h):
            row_base = y * w
            for x in range(w):
                dx = x - 160
                dy = y - 120
                v = (
                    math.sin((x + t * 1.5) * 0.045)
                    + math.sin((y - t * 1.2) * 0.04)
                    + math.sin((x + y) * 0.02 + phase)
                    + math.sin(math.sqrt(dx * dx + dy * dy) * 0.08 - phase * 1.3)
                )
                c = int((v + 4.0) * (255.0 / 8.0))
                if c < 0:
                    c = 0
                if c > 255:
                    c = 255
                frame[row_base + x] = c
        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_15_wave_interference_loop()
