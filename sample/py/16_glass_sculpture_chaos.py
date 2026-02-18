# 16: ガラス彫刻のカオス回転をレイトレーシングで描き、GIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from pylib.gif import save_gif


def clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def dot(ax: float, ay: float, az: float, bx: float, by: float, bz: float) -> float:
    return ax * bx + ay * by + az * bz


def length(x: float, y: float, z: float) -> float:
    return math.sqrt(x * x + y * y + z * z)


def normalize(x: float, y: float, z: float) -> tuple[float, float, float]:
    l = length(x, y, z)
    if l < 1e-9:
        return 0.0, 0.0, 0.0
    return x / l, y / l, z / l


def reflect(ix: float, iy: float, iz: float, nx: float, ny: float, nz: float) -> tuple[float, float, float]:
    d = dot(ix, iy, iz, nx, ny, nz) * 2.0
    return ix - d * nx, iy - d * ny, iz - d * nz


def refract(ix: float, iy: float, iz: float, nx: float, ny: float, nz: float, eta: float) -> tuple[float, float, float]:
    # IOR 由来の簡易屈折。全反射時は反射方向を返す。
    cosi = -dot(ix, iy, iz, nx, ny, nz)
    sint2 = eta * eta * (1.0 - cosi * cosi)
    if sint2 > 1.0:
        return reflect(ix, iy, iz, nx, ny, nz)
    cost = math.sqrt(1.0 - sint2)
    k = eta * cosi - cost
    return eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz


def schlick(cos_theta: float, f0: float) -> float:
    m = 1.0 - cos_theta
    return f0 + (1.0 - f0) * (m * m * m * m * m)


def sky_color(dx: float, dy: float, dz: float, tphase: float) -> tuple[float, float, float]:
    # 上空グラデーション + ネオン帯
    t = 0.5 * (dy + 1.0)
    r = 0.06 + 0.20 * t
    g = 0.10 + 0.25 * t
    b = 0.16 + 0.45 * t
    band = 0.5 + 0.5 * math.sin(8.0 * dx + 6.0 * dz + tphase)
    r += 0.08 * band
    g += 0.05 * band
    b += 0.12 * band
    return clamp01(r), clamp01(g), clamp01(b)


def sphere_intersect(
    ox: float,
    oy: float,
    oz: float,
    dx: float,
    dy: float,
    dz: float,
    cx: float,
    cy: float,
    cz: float,
    radius: float,
) -> float:
    lx = ox - cx
    ly = oy - cy
    lz = oz - cz
    b = lx * dx + ly * dy + lz * dz
    c = lx * lx + ly * ly + lz * lz - radius * radius
    h = b * b - c
    if h < 0.0:
        return -1.0
    s = math.sqrt(h)
    t0 = -b - s
    if t0 > 1e-4:
        return t0
    t1 = -b + s
    if t1 > 1e-4:
        return t1
    return -1.0


def palette_332() -> bytes:
    # 3-3-2 量子化パレット。量子化処理が軽く、トランスパイル後も高速。
    p = bytearray(256 * 3)
    for i in range(256):
        r = (i >> 5) & 7
        g = (i >> 2) & 7
        b = i & 3
        p[i * 3 + 0] = int((255 * r) / 7)
        p[i * 3 + 1] = int((255 * g) / 7)
        p[i * 3 + 2] = int((255 * b) / 3)
    return bytes(p)


def quantize_332(r: float, g: float, b: float) -> int:
    rr = int(clamp01(r) * 255.0)
    gg = int(clamp01(g) * 255.0)
    bb = int(clamp01(b) * 255.0)
    return ((rr >> 5) << 5) + ((gg >> 5) << 2) + (bb >> 6)


def render_frame(width: int, height: int, frame_id: int, frames_n: int) -> bytes:
    t = frame_id / frames_n
    tphase = 2.0 * math.pi * t

    # カメラはゆっくり周回
    cam_r = 3.0
    cam_x = cam_r * math.cos(tphase * 0.9)
    cam_y = 1.1 + 0.25 * math.sin(tphase * 0.6)
    cam_z = cam_r * math.sin(tphase * 0.9)
    look_x = 0.0
    look_y = 0.35
    look_z = 0.0

    fwd_x, fwd_y, fwd_z = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z)
    right_x, right_y, right_z = normalize(fwd_z, 0.0, -fwd_x)
    up_x, up_y, up_z = normalize(
        right_y * fwd_z - right_z * fwd_y,
        right_z * fwd_x - right_x * fwd_z,
        right_x * fwd_y - right_y * fwd_x,
    )

    # 動くガラス彫刻（3球）と発光球
    s0x = 0.9 * math.cos(1.3 * tphase)
    s0y = 0.15 + 0.35 * math.sin(1.7 * tphase)
    s0z = 0.9 * math.sin(1.3 * tphase)
    s1x = 1.2 * math.cos(1.3 * tphase + 2.094)
    s1y = 0.10 + 0.40 * math.sin(1.1 * tphase + 0.8)
    s1z = 1.2 * math.sin(1.3 * tphase + 2.094)
    s2x = 1.0 * math.cos(1.3 * tphase + 4.188)
    s2y = 0.20 + 0.30 * math.sin(1.5 * tphase + 1.9)
    s2z = 1.0 * math.sin(1.3 * tphase + 4.188)
    lr = 0.35
    lx = 2.4 * math.cos(tphase * 1.8)
    ly = 1.8 + 0.8 * math.sin(tphase * 1.2)
    lz = 2.4 * math.sin(tphase * 1.8)

    frame = bytearray(width * height)
    aspect = width / height
    fov = 1.25

    i = 0
    for py in range(height):
        sy = 1.0 - (2.0 * (py + 0.5) / height)
        for px in range(width):
            sx = (2.0 * (px + 0.5) / width - 1.0) * aspect
            rx = fwd_x + fov * (sx * right_x + sy * up_x)
            ry = fwd_y + fov * (sx * right_y + sy * up_y)
            rz = fwd_z + fov * (sx * right_z + sy * up_z)
            dx, dy, dz = normalize(rx, ry, rz)

            # 最短ヒットを探索
            best_t = 1e9
            hit_kind = 0  # 0:sky, 1:floor, 2/3/4:glass sphere
            r = 0.0
            g = 0.0
            b = 0.0

            # 床平面 y=-1.2
            if dy < -1e-6:
                tf = (-1.2 - cam_y) / dy
                if tf > 1e-4 and tf < best_t:
                    best_t = tf
                    hit_kind = 1

            t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65)
            if t0 > 0.0 and t0 < best_t:
                best_t = t0
                hit_kind = 2
            t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72)
            if t1 > 0.0 and t1 < best_t:
                best_t = t1
                hit_kind = 3
            t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58)
            if t2 > 0.0 and t2 < best_t:
                best_t = t2
                hit_kind = 4

            if hit_kind == 0:
                r, g, b = sky_color(dx, dy, dz, tphase)
            elif hit_kind == 1:
                hx = cam_x + best_t * dx
                hz = cam_z + best_t * dz
                cx = int(math.floor(hx * 2.0))
                cz = int(math.floor(hz * 2.0))
                checker = 0 if (cx + cz) % 2 == 0 else 1
                base_r = 0.10 if checker == 0 else 0.04
                base_g = 0.11 if checker == 0 else 0.05
                base_b = 0.13 if checker == 0 else 0.08
                # 発光球の寄与
                lxv = lx - hx
                lyv = ly - (-1.2)
                lzv = lz - hz
                ldx, ldy, ldz = normalize(lxv, lyv, lzv)
                ndotl = max(ldy, 0.0)
                ldist2 = lxv * lxv + lyv * lyv + lzv * lzv
                glow = 8.0 / (1.0 + ldist2)
                r = base_r + 0.8 * glow + 0.20 * ndotl
                g = base_g + 0.5 * glow + 0.18 * ndotl
                b = base_b + 1.0 * glow + 0.24 * ndotl
            else:
                cx = 0.0
                cy = 0.0
                cz = 0.0
                rad = 1.0
                if hit_kind == 2:
                    cx = s0x
                    cy = s0y
                    cz = s0z
                    rad = 0.65
                elif hit_kind == 3:
                    cx = s1x
                    cy = s1y
                    cz = s1z
                    rad = 0.72
                else:
                    cx = s2x
                    cy = s2y
                    cz = s2z
                    rad = 0.58
                hx = cam_x + best_t * dx
                hy = cam_y + best_t * dy
                hz = cam_z + best_t * dz
                nx, ny, nz = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad)

                # 簡易ガラスシェーディング（反射+屈折+光源ハイライト）
                rdx, rdy, rdz = reflect(dx, dy, dz, nx, ny, nz)
                tdx, tdy, tdz = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45)
                sr, sg, sb = sky_color(rdx, rdy, rdz, tphase)
                tr, tg, tb = sky_color(tdx, tdy, tdz, tphase + 0.8)
                cosi = max(-(dx * nx + dy * ny + dz * nz), 0.0)
                fr = schlick(cosi, 0.04)
                r = tr * (1.0 - fr) + sr * fr
                g = tg * (1.0 - fr) + sg * fr
                b = tb * (1.0 - fr) + sb * fr

                lxv = lx - hx
                lyv = ly - hy
                lzv = lz - hz
                ldx, ldy, ldz = normalize(lxv, lyv, lzv)
                ndotl = max(nx * ldx + ny * ldy + nz * ldz, 0.0)
                hvx, hvy, hvz = normalize(ldx - dx, ldy - dy, ldz - dz)
                ndoth = max(nx * hvx + ny * hvy + nz * hvz, 0.0)
                spec = ndoth * ndoth
                spec = spec * spec
                spec = spec * spec
                spec = spec * spec
                glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv)
                r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow
                g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow
                b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow

                # 球ごとに僅かな色味差
                if hit_kind == 2:
                    r *= 0.95
                    g *= 1.05
                    b *= 1.10
                elif hit_kind == 3:
                    r *= 1.08
                    g *= 0.98
                    b *= 1.04
                else:
                    r *= 1.02
                    g *= 1.10
                    b *= 0.95

            # やや強めのトーンマップ
            r = math.sqrt(clamp01(r))
            g = math.sqrt(clamp01(g))
            b = math.sqrt(clamp01(b))
            frame[i] = quantize_332(r, g, b)
            i += 1

    return bytes(frame)


def run_16_glass_sculpture_chaos() -> None:
    width = 320
    height = 240
    frames_n = 72
    out_path = "sample/out/16_glass_sculpture_chaos.gif"

    start = perf_counter()
    frames: list[bytes] = []
    for i in range(frames_n):
        frames.append(render_frame(width, height, i, frames_n))

    save_gif(out_path, width, height, frames, palette_332(), delay_cs=6, loop=0)
    elapsed = perf_counter() - start
    print("output:", out_path)
    print("frames:", frames_n)
    print("elapsed_sec:", elapsed)


if __name__ == "__main__":
    run_16_glass_sculpture_chaos()
