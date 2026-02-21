# 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

from __future__ import annotations

from time import perf_counter

from pytra.runtime.gif import grayscale_palette, save_gif


def render_frame(width: int, height: int, center_x: float, center_y: float, scale: float, max_iter: int) -> bytes:
    frame = bytearray(width * height)
    idx = 0
    for y in range(height):
        cy = center_y + (y - height * 0.5) * scale
        for x in range(width):
            cx = center_x + (x - width * 0.5) * scale
            zx = 0.0
            zy = 0.0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                i += 1
            frame[idx] = int((255.0 * i) / max_iter)
            idx += 1
    return bytes(frame)


def run_05_mandelbrot_zoom() -> None:
    width = 320
    height = 240
    frame_count = 48
    max_iter = 110
    center_x = -0.743643887037151
    center_y = 0.13182590420533
    base_scale = 3.2 / width
    zoom_per_frame = 0.93
    out_path = "sample/out/05_mandelbrot_zoom.gif"

    start = perf_counter()
    frames: list[bytes] = []
    scale = base_scale
    for _ in range(frame_count):
        frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
        scale *= zoom_per_frame

    save_gif(out_path, width, height, frames, grayscale_palette(), delay_cs=5, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frame_count)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_05_mandelbrot_zoom()
