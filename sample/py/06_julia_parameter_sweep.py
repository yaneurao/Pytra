# 06: Sample that sweeps Julia-set parameters and outputs a GIF.

from __future__ import annotations

import math
from time import perf_counter

from pytra.runtime.gif import save_gif


def julia_palette() -> bytes:
    # Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
    palette = bytearray(256 * 3)
    palette[0] = 0
    palette[1] = 0
    palette[2] = 0
    for i in range(1, 256):
        t = (i - 1) / 254.0
        r = int(255.0 * (9.0 * (1.0 - t) * t * t * t))
        g = int(255.0 * (15.0 * (1.0 - t) * (1.0 - t) * t * t))
        b = int(255.0 * (8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t))
        palette[i * 3 + 0] = r
        palette[i * 3 + 1] = g
        palette[i * 3 + 2] = b
    return bytes(palette)


def render_frame(width: int, height: int, cr: float, ci: float, max_iter: int, phase: int) -> bytes:
    frame = bytearray(width * height)
    idx = 0
    for y in range(height):
        zy0 = -1.2 + 2.4 * (y / (height - 1))
        for x in range(width):
            zx = -1.8 + 3.6 * (x / (width - 1))
            zy = zy0
            i = 0
            while i < max_iter:
                zx2 = zx * zx
                zy2 = zy * zy
                if zx2 + zy2 > 4.0:
                    break
                zy = 2.0 * zx * zy + ci
                zx = zx2 - zy2 + cr
                i += 1
            if i >= max_iter:
                frame[idx] = 0
            else:
                # Add a small frame phase so colors flow smoothly.
                color_index = 1 + (((i * 224) // max_iter + phase) % 255)
                frame[idx] = color_index
            idx += 1
    return bytes(frame)


def run_06_julia_parameter_sweep() -> None:
    width = 320
    height = 240
    frames_n = 72
    max_iter = 180
    out_path = "sample/out/06_julia_parameter_sweep.gif"

    start = perf_counter()
    frames: list[bytes] = []
    # Orbit an ellipse around a known visually good region to reduce flat blown highlights.
    center_cr = -0.745
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.10
    # Add start and phase offsets so GitHub thumbnails do not appear too dark.
    # Tune it to start in a red-leaning color range.
    start_offset = 20
    phase_offset = 180
    for i in range(frames_n):
        t = ((i + start_offset) % frames_n) / frames_n
        angle = 2.0 * math.pi * t
        cr = center_cr + radius_cr * math.cos(angle)
        ci = center_ci + radius_ci * math.sin(angle)
        phase = (phase_offset + i * 5) % 255
        frames.append(render_frame(width, height, cr, ci, max_iter, phase))

    save_gif(out_path, width, height, frames, julia_palette(), delay_cs=8, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_06_julia_parameter_sweep()
