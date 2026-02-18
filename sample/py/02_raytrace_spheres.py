# 02: 球のみのミニレイトレーサを実行し、PNG画像を出力するサンプルです。
# トランスパイル互換のため、依存モジュールは最小限（timeのみ）にしています。

import math
from pylib import png_helper
from time import perf_counter


def clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def hit_sphere(ox: float, oy: float, oz: float, dx: float, dy: float, dz: float, cx: float, cy: float, cz: float, r: float) -> float:
    """レイと球の交差距離t（交差しない場合は-1）を返す。"""
    lx: float = ox - cx
    ly: float = oy - cy
    lz: float = oz - cz

    a: float = dx * dx + dy * dy + dz * dz
    b: float = 2.0 * (lx * dx + ly * dy + lz * dz)
    c: float = lx * lx + ly * ly + lz * lz - r * r

    d: float = b * b - 4.0 * a * c
    if d < 0.0:
        return -1.0

    sd: float = math.sqrt(d)
    t0: float = (-b - sd) / (2.0 * a)
    t1: float = (-b + sd) / (2.0 * a)

    if t0 > 0.001:
        return t0
    if t1 > 0.001:
        return t1
    return -1.0


def render(width: int, height: int, aa: int) -> bytearray:
    pixels: bytearray = bytearray()

    # カメラ原点
    ox: float = 0.0
    oy: float = 0.0
    oz: float = -3.0

    # ライト方向（正規化済み）
    lx: float = -0.4
    ly: float = 0.8
    lz: float = -0.45

    for y in range(height):
        for x in range(width):
            ar: int = 0
            ag: int = 0
            ab: int = 0

            for ay in range(aa):
                for ax in range(aa):
                    fy = (y + (ay + 0.5) / aa) / (height - 1)
                    fx = (x + (ax + 0.5) / aa) / (width - 1)
                    sy: float = 1.0 - 2.0 * fy
                    sx: float = (2.0 * fx - 1.0) * (width / height)

                    dx: float = sx
                    dy: float = sy
                    dz: float = 1.0
                    inv_len: float = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz)
                    dx *= inv_len
                    dy *= inv_len
                    dz *= inv_len

                    t_min: float = 1.0e30
                    hit_id: int = -1

                    t: float = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8)
                    if t > 0.0 and t < t_min:
                        t_min = t
                        hit_id = 0

                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
                    if t > 0.0 and t < t_min:
                        t_min = t
                        hit_id = 1

                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0)
                    if t > 0.0 and t < t_min:
                        t_min = t
                        hit_id = 2

                    r: int = 0
                    g: int = 0
                    b: int = 0

                    if hit_id >= 0:
                        px: float = ox + dx * t_min
                        py: float = oy + dy * t_min
                        pz: float = oz + dz * t_min

                        nx: float = 0.0
                        ny: float = 0.0
                        nz: float = 0.0

                        if hit_id == 0:
                            nx = (px + 0.8) / 0.8
                            ny = (py + 0.2) / 0.8
                            nz = (pz - 2.2) / 0.8
                        elif hit_id == 1:
                            nx = (px - 0.9) / 0.95
                            ny = (py - 0.1) / 0.95
                            nz = (pz - 2.9) / 0.95
                        else:
                            nx = 0.0
                            ny = 1.0
                            nz = 0.0

                        diff: float = nx * (-lx) + ny * (-ly) + nz * (-lz)
                        diff = clamp01(diff)

                        base_r: float = 0.0
                        base_g: float = 0.0
                        base_b: float = 0.0

                        if hit_id == 0:
                            base_r = 0.95
                            base_g = 0.35
                            base_b = 0.25
                        elif hit_id == 1:
                            base_r = 0.25
                            base_g = 0.55
                            base_b = 0.95
                        else:
                            checker: int = int((px + 50.0) * 0.8) + int((pz + 50.0) * 0.8)
                            if checker % 2 == 0:
                                base_r = 0.85
                                base_g = 0.85
                                base_b = 0.85
                            else:
                                base_r = 0.2
                                base_g = 0.2
                                base_b = 0.2

                        shade: float = 0.12 + 0.88 * diff
                        r = int(255.0 * clamp01(base_r * shade))
                        g = int(255.0 * clamp01(base_g * shade))
                        b = int(255.0 * clamp01(base_b * shade))
                    else:
                        tsky: float = 0.5 * (dy + 1.0)
                        r = int(255.0 * (0.65 + 0.20 * tsky))
                        g = int(255.0 * (0.75 + 0.18 * tsky))
                        b = int(255.0 * (0.90 + 0.08 * tsky))

                    ar += r
                    ag += g
                    ab += b

            samples = aa * aa
            pixels.append(ar // samples)
            pixels.append(ag // samples)
            pixels.append(ab // samples)

    return pixels


def run_raytrace() -> None:
    width: int = 1600
    height: int = 900
    aa: int = 2
    out_path: str = "sample/out/raytrace_02.png"

    start: float = perf_counter()
    pixels: bytearray = render(width, height, aa)
    png_helper.write_rgb_png(out_path, width, height, pixels)
    elapsed: float = perf_counter() - start

    print("output:", out_path)
    print("size:", width, "x", height)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_raytrace()
