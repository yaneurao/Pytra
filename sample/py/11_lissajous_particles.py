# 11: リサージュ運動する粒子をGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


def color_palette() -> bytes:
    p = bytearray()
    i = 0
    while i < 256:
        r = i
        g = (i * 3) % 256
        b = 255 - i
        p.extend((r, g, b))
        i += 1
    return bytes(p)


def main() -> None:
    w = 320
    h = 240
    frames_n = 80
    particles = 24
    out_path = "sample/out/11_lissajous_particles.gif"

    start = perf_counter()
    frames: list[bytes] = []

    t = 0
    while t < frames_n:
        frame = bytearray(w * h)

        p = 0
        while p < particles:
            phase = p * 0.261799
            x = int((w * 0.5) + (w * 0.38) * math.sin(0.11 * t + phase * 2.0))
            y = int((h * 0.5) + (h * 0.38) * math.sin(0.17 * t + phase * 3.0))
            color = 30 + (p * 9) % 220

            dy = -2
            while dy <= 2:
                dx = -2
                while dx <= 2:
                    xx = x + dx
                    yy = y + dy
                    if 0 <= xx < w and 0 <= yy < h:
                        d2 = dx * dx + dy * dy
                        if d2 <= 4:
                            idx = yy * w + xx
                            v = color - d2 * 20
                            if v < 0:
                                v = 0
                            if v > frame[idx]:
                                frame[idx] = v
                    dx += 1
                dy += 1

            p += 1

        frames.append(bytes(frame))
        t += 1

    save_gif(out_path, w, h, frames, color_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    main()
