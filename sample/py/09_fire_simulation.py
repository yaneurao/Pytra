# 09: 簡易ファイアエフェクトをGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import save_gif


def fire_palette() -> bytes:
    p = bytearray()
    i = 0
    while i < 256:
        if i < 85:
            r = i * 3
            g = 0
            b = 0
        elif i < 170:
            r = 255
            g = (i - 85) * 3
            b = 0
        else:
            r = 255
            g = 255
            b = (i - 170) * 3
        p.extend((r, g, b))
        i += 1
    return bytes(p)


def main() -> None:
    w = 220
    h = 140
    steps = 110
    out_path = "sample/out/09_fire_simulation.gif"

    start = perf_counter()
    heat = [[0 for _ in range(w)] for _ in range(h)]
    frames: list[bytes] = []

    t = 0
    while t < steps:
        x = 0
        while x < w:
            val = 170 + ((x * 13 + t * 17) % 86)
            heat[h - 1][x] = val
            x += 1

        y = 1
        while y < h:
            x = 0
            while x < w:
                a = heat[y][x]
                b = heat[y][(x - 1 + w) % w]
                c = heat[y][(x + 1) % w]
                d = heat[(y + 1) % h][x]
                v = (a + b + c + d) // 4
                cool = 1 + ((x + y + t) % 3)
                nv = v - cool
                heat[y - 1][x] = nv if nv > 0 else 0
                x += 1
            y += 1

        frame = bytearray(w * h)
        i = 0
        yy = 0
        while yy < h:
            xx = 0
            while xx < w:
                frame[i] = heat[yy][xx]
                i += 1
                xx += 1
            yy += 1
        frames.append(bytes(frame))
        t += 1

    save_gif(out_path, w, h, frames, fire_palette(), delay_cs=4, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", steps)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    main()
