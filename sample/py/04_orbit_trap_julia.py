# 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

from __future__ import annotations

from time import perf_counter

from pytra.utils import png


def render_orbit_trap_julia(width: int, height: int, max_iter: int, cx: float, cy: float) -> bytearray:
    pixels: bytearray = bytearray()

    for y in range(height):
        zy0: float = -1.3 + 2.6 * (y / (height - 1))
        for x in range(width):
            zx: float = -1.9 + 3.8 * (x / (width - 1))
            zy: float = zy0

            trap: float = 1.0e9
            i: int = 0
            while i < max_iter:
                ax: float = zx
                if ax < 0.0:
                    ax = -ax
                ay: float = zy
                if ay < 0.0:
                    ay = -ay
                dxy: float = zx - zy
                if dxy < 0.0:
                    dxy = -dxy

                if ax < trap:
                    trap = ax
                if ay < trap:
                    trap = ay
                if dxy < trap:
                    trap = dxy

                zx2: float = zx * zx
                zy2: float = zy * zy
                if zx2 + zy2 > 4.0:
                    break

                zy = 2.0 * zx * zy + cy
                zx = zx2 - zy2 + cx
                i += 1

            r: int = 0
            g: int = 0
            b: int = 0
            if i >= max_iter:
                r = 0
                g = 0
                b = 0
            else:
                trap_scaled: float = trap * 3.2
                if trap_scaled > 1.0:
                    trap_scaled = 1.0
                if trap_scaled < 0.0:
                    trap_scaled = 0.0

                t: float = i / max_iter
                tone: int = int(255.0 * (1.0 - trap_scaled))
                r = int(tone * (0.35 + 0.65 * t))
                g = int(tone * (0.15 + 0.85 * (1.0 - t)))
                b = int(255.0 * (0.25 + 0.75 * t))
                if r > 255:
                    r = 255
                if g > 255:
                    g = 255
                if b > 255:
                    b = 255

            pixels.append(r)
            pixels.append(g)
            pixels.append(b)

    return pixels


def run_04_orbit_trap_julia() -> None:
    width: int = 1920
    height: int = 1080
    max_iter: int = 1400
    out_path: str = "sample/out/04_orbit_trap_julia.png"

    start: float = perf_counter()
    pixels: bytearray = render_orbit_trap_julia(width, height, max_iter, -0.7269, 0.1889)
    png.write_rgb_png(out_path, width, height, pixels)
    elapsed: float = perf_counter() - start

    print("output:", out_path)
    print("size:", width, "x", height)
    print("max_iter:", max_iter)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_04_orbit_trap_julia()
