# 11: Sample that outputs Lissajous-motion particles as a GIF.

from __future__ import annotations

import math
from time import perf_counter

from pytra.runtime.gif import save_gif


def color_palette() -> bytes:
    p = bytearray()
    for i in range(256):
        r = i
        g = (i * 3) % 256
        b = 255 - i
        p.append(r)
        p.append(g)
        p.append(b)
    return bytes(p)


def run_11_lissajous_particles() -> None:
    w = 320
    h = 240
    frames_n = 360
    particles = 48
    out_path = "sample/out/11_lissajous_particles.gif"

    start = perf_counter()
    frames: list[bytes] = []

    for t in range(frames_n):
        frame = bytearray(w * h)

        for p in range(particles):
            phase = p * 0.261799
            x = int((w * 0.5) + (w * 0.38) * math.sin(0.11 * t + phase * 2.0))
            y = int((h * 0.5) + (h * 0.38) * math.sin(0.17 * t + phase * 3.0))
            color = 30 + (p * 9) % 220

            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    xx = x + dx
                    yy = y + dy
                    if xx >= 0 and xx < w and yy >= 0 and yy < h:
                        d2 = dx * dx + dy * dy
                        if d2 <= 4:
                            idx = yy * w + xx
                            v = color - d2 * 20
                            v = max(0, v)
                            if v > frame[idx]:
                                frame[idx] = v

        frames.append(bytes(frame))

    save_gif(out_path, w, h, frames, color_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_11_lissajous_particles()
