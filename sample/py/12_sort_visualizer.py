# 12: バブルソートの途中状態をGIF出力するサンプル。

from __future__ import annotations

from time import perf_counter

from py_module.gif_helper import grayscale_palette, save_gif


def render(values: list[int], w: int, h: int) -> bytes:
    frame = bytearray(w * h)
    n = len(values)
    bar_w = w / n
    i = 0
    while i < n:
        x0 = int(i * bar_w)
        x1 = int((i + 1) * bar_w)
        if x1 <= x0:
            x1 = x0 + 1
        bh = int(((values[i] / n) * h))
        y = h - bh
        while y < h:
            x = x0
            while x < x1:
                frame[y * w + x] = 255
                x += 1
            y += 1
        i += 1
    return bytes(frame)


def run_12_sort_visualizer() -> None:
    w = 320
    h = 180
    n = 72
    out_path = "sample/out/12_sort_visualizer.gif"

    start = perf_counter()
    values: list[int] = []
    i = 0
    while i < n:
        values.append((i * 37 + 19) % n)
        i += 1

    frames: list[bytes] = [render(values, w, h)]

    i = 0
    op = 0
    while i < n:
        j = 0
        swapped = False
        while j < n - i - 1:
            if values[j] > values[j + 1]:
                tmp = values[j]
                values[j] = values[j + 1]
                values[j + 1] = tmp
                swapped = True
            if op % 8 == 0:
                frames.append(render(values, w, h))
            op += 1
            j += 1
        if not swapped:
            break
        i += 1

    save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs=3, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", len(frames))
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_12_sort_visualizer()
