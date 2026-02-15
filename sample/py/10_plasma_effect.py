# 10: プラズマエフェクトをGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from gif_helper import grayscale_palette, save_gif


def main() -> None:
    w = 320
    h = 240
    frames_n = 72
    out_path = "sample/out/10_plasma_effect.gif"

    start = perf_counter()
    frames: list[bytes] = []

    t = 0
    while t < frames_n:
        frame = bytearray(w * h)
        i = 0
        y = 0
        while y < h:
            x = 0
            while x < w:
                v = (
                    math.sin((x + t * 2.0) * 0.045)
                    + math.sin((y - t * 1.2) * 0.05)
                    + math.sin((x + y + t * 1.7) * 0.03)
                    + math.sin(math.sqrt((x - 160) ** 2 + (y - 120) ** 2) * 0.07 - t * 0.18)
                )
                c = int((v + 4.0) * (255.0 / 8.0))
                if c < 0:
                    c = 0
                if c > 255:
                    c = 255
                frame[i] = c
                i += 1
                x += 1
            y += 1
        frames.append(bytes(frame))
        t += 1

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    main()
