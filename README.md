<a href="docs/ja/README.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/README-日本語-2563EB?style=flat-square">
</a>

<p align="center">
  <img src="docs/images/pytra-code-alchemist-s.png" alt="Pytra Code Alchemist" width="256">
</p>

<div align="center">
    <h1>Pytra</h1>
    <img alt="Python" src="https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white"> (subset) is the source language for Pytra, which transpiles code into multiple target languages.
    <p><a href="docs/en/index.md">Read the Docs</a></p>
</div>

<div align="center">
    <img alt="C++" src="https://img.shields.io/badge/-C%2B%2B%C2%A0%C2%A0%C2%A0-00599C?style=flat-square&logo=cplusplus&logoColor=white">
    <img alt="Rust" src="https://img.shields.io/badge/-Rust%C2%A0%C2%A0-F6B73C?style=flat-square&logo=rust&logoColor=black">
    <img alt="C#" src="https://img.shields.io/badge/-C%23%C2%A0%C2%A0%C2%A0%C2%A0-239120?style=flat-square&logo=dotnet&logoColor=white">
    <img alt="JS" src="https://img.shields.io/badge/-JS%C2%A0%C2%A0%C2%A0%C2%A0-F7DF1E?style=flat-square&logo=javascript&logoColor=black">
    <img alt="TS" src="https://img.shields.io/badge/-TS%C2%A0%C2%A0%C2%A0%C2%A0-3178C6?style=flat-square&logo=typescript&logoColor=white">
    <img alt="Go" src="https://img.shields.io/badge/-Go%C2%A0%C2%A0%C2%A0%C2%A0-00ADD8?style=flat-square&logo=go&logoColor=white">
    <br>
    <img alt="Java" src="https://img.shields.io/badge/-Java%C2%A0%C2%A0-ED8B00?style=flat-square&logo=openjdk&logoColor=white">
    <img alt="Swift" src="https://img.shields.io/badge/-Swift%C2%A0-F05138?style=flat-square&logo=swift&logoColor=white">
    <img alt="Kotlin" src="https://img.shields.io/badge/-Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white">
    <img alt="Ruby" src="https://img.shields.io/badge/-Ruby%C2%A0%C2%A0-BB1200?style=flat-square&logo=ruby&logoColor=white">
    <img alt="Lua" src="https://img.shields.io/badge/-Lua%C2%A0%C2%A0%C2%A0-4C6EF5?style=flat-square&logo=lua&logoColor=white">
    <img alt="Scala3" src="https://img.shields.io/badge/-Scala3-10B981?style=flat-square&logo=scala&logoColor=white">
    <img alt="PHP" src="https://img.shields.io/badge/-PHP%C2%A0%C2%A0%C2%A0-777BB4?style=flat-square&logo=php&logoColor=white">
</div>

## Latest News

> **2026-03-02 | v0.6.0 Released**  
> Version 0.6.0 was released, adding Scala as a supported target language.

> **2026-03-01 | v0.5.0 Released**  
> Version 0.5.0 was released, adding Lua as a supported target language.

> **2026-02-28 | v0.4.0 Released**  
> Version 0.4.0 was released, adding Ruby as a supported target language.

- Past News: [docs/en/news/index.md](docs/en/news/index.md)

## Features

Pytra's features

- Python to multi-language transpiler
  - Supports conversion to C++, C#, Rust, JavaScript, TypeScript, Go, Java, Swift, Kotlin, Ruby, Lua, Scala3, and PHP.
  - Converts code to output in a form extremely close to the original source.

- Write Python code that targets C++-level output quality
  - `int` defaults to 64-bit signed integer.
  - No dynamic typing.

- Simple language model
  - Basically a subset of Python.
  - Can be developed with existing tools such as VS Code.
  - Drops multiple inheritance and keeps only single inheritance.

- High extensibility
  - The transpiler core is implemented in Python, making extension and customization easy.
  - The transpiler's own source code can be transpiled into other languages by this transpiler, enabling self-hosting.

We also prioritize practical operational benefits.

WARNING: This project is still under active development and may be far from production-ready. Review sample code first and use at your own risk.

WARNING: Do not expect entire Python applications to be portable as-is. A realistic expectation is: if the core logic you wrote in Python transpiles well, that is a good outcome.

## Runtime Performance Comparison

Execution times for [sample programs](sample/readme.md) written in Python and their transpiled versions (unit: seconds). In the table, Python is the original code and PyPy is for reference.

|No.|Workload|Python|PyPy| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin | Ruby | Lua | Scala3 |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |Mandelbrot set (PNG)|18.647|1.091|0.790|0.781|0.383|0.768|0.806|0.753|0.756|0.760|0.756|18.955|5.500|2.221|
|02 |Simple sphere ray tracer (PNG)|6.890|0.529|0.202|0.165|0.918|0.277|0.288|0.256|0.260|0.289|0.258|11.146|3.049|15.765|
|03 |Julia set (PNG)|22.770|1.959|0.861|0.823|1.468|1.210|1.127|1.126|1.136|1.125|1.151|37.170|8.162|7.935|
|04 |Orbit-trap Julia set (PNG)|11.950|1.081|0.380|0.358|0.416|0.473|0.504|0.466|0.471|0.482|0.469|28.702|4.237|7.592|
|05 |Mandelbrot zoom (GIF)|14.538|1.262|0.555|0.569|1.710|0.703|0.680|0.691|0.689|0.695|0.687|14.892|17.852|8.871|
|06 |Julia parameter sweep (GIF)|9.627|0.507|0.546|0.407|0.329|0.626|0.619|0.622|0.621|0.624|0.629|10.704|11.122|11.067|
|07 |Game of Life (GIF)|5.134|0.685|0.363|0.369|1.530|1.364|1.311|1.191|1.248|1.290|1.267|11.205|8.036|5.225|
|08 |Langton's Ant (GIF)|5.220|0.767|0.452|0.483|2.213|2.031|1.997|1.912|2.011|1.886|2.019|18.824|10.367|6.446|
|09 |Flame simulation (GIF)|10.895|1.167|0.611|0.661|6.566|2.374|2.290|2.368|2.265|2.306|2.358|32.077|18.097|18.956|
|10 |Plasma effect (GIF)|6.194|0.876|0.684|0.554|2.646|1.444|1.886|1.397|1.414|1.444|1.319|11.745|7.806|4.525|
|11 |Lissajous particles (GIF)|3.582|0.532|0.356|0.359|0.714|1.425|1.406|1.389|1.365|1.371|1.413|7.950|7.809|3.406|
|12 |Sorting visualization (GIF)|3.864|0.552|0.344|0.362|0.680|1.341|1.343|1.309|1.348|1.328|1.306|8.087|7.078|4.057|
|13 |Maze generation steps (GIF)|3.402|0.533|0.287|0.298|1.037|1.038|1.035|0.985|1.025|0.997|0.987|6.825|6.288|3.735|
|14 |Simple ray marching (GIF)|2.670|0.300|0.160|0.159|0.606|0.489|0.573|0.490|0.513|0.503|0.492|3.800|3.370|2.138|
|15 |Wave interference loop (GIF)|2.631|0.402|0.299|0.252|1.196|0.616|0.794|0.609|0.614|0.629|0.612|5.142|3.316|2.496|
|16 |Chaos rotation of glass sculpture (GIF)|6.847|0.606|0.277|0.246|1.220|0.650|0.822|0.638|0.643|0.667|0.643|8.743|8.059|15.675|
|17 |Monte Carlo Pi approximation|2.981|0.105|0.019|0.018|0.098|0.431|0.433|0.432|0.433|0.436|0.436|1.988|0.534|0.279|
|18 |Mini-language interpreter|2.037|0.601|0.610|0.427|0.735|0.446|0.446|0.405|0.417|0.423|0.417|7.854|2.403|0.885|

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>Sample code: 06_julia_parameter_sweep.py</summary>

```python
# 06: Sweep Julia-set parameters and output an animated GIF.

from __future__ import annotations

import math
from time import perf_counter

from pylib.tra.gif import save_gif


def julia_palette() -> bytes:
    # Keep index 0 black for points inside the set; use vivid gradients for the rest.
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
                # Add frame phase so color flow stays smooth across frames.
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
    # Circle around a known good region using an elliptical path to avoid flat blown-out frames.
    center_cr = -0.745
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.10
    # Add offsets so GitHub thumbnails do not look too dark.
    # Tuned to start from a red-leaning color region.
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
```
</details>

<details>
<summary>Transpiled code (C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby)</summary>

- C++: [View full code](sample/cpp/06_julia_parameter_sweep.cpp)
- Rust: [View full code](sample/rs/06_julia_parameter_sweep.rs)
- C#: [View full code](sample/cs/06_julia_parameter_sweep.cs)
- JavaScript: [View full code](sample/js/06_julia_parameter_sweep.js)
- TypeScript: [View full code](sample/ts/06_julia_parameter_sweep.ts)
- Go: [View full code](sample/go/06_julia_parameter_sweep.go)
- Java: [View full code](sample/java/06_julia_parameter_sweep.java)
- Swift: [View full code](sample/swift/06_julia_parameter_sweep.swift)
- Kotlin: [View full code](sample/kotlin/06_julia_parameter_sweep.kt)
- Ruby: [View full code](sample/ruby/06_julia_parameter_sweep.rb)

</details>

<br/>

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>Sample code: 16_glass_sculpture_chaos.py</summary>

```python
# 16: Render chaotic rotation of glass sculptures with ray tracing and output a GIF.

from __future__ import annotations

import math
from time import perf_counter

from pylib.tra.gif import save_gif


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
    # Simple IOR-based refraction. Falls back to reflection for total internal reflection.
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
    # Sky gradient plus neon banding.
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
    # 3-3-2 quantized palette: lightweight quantization and fast after transpilation.
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

    # Camera slowly orbits the scene.
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

    # Moving glass sculpture (3 spheres) and an emissive light sphere.
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

            # Search nearest hit.
            best_t = 1e9
            hit_kind = 0  # 0: sky, 1: floor, 2/3/4: glass spheres
            r = 0.0
            g = 0.0
            b = 0.0

            # Floor plane y=-1.2
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
                # Emissive sphere contribution
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

                # Simplified glass shading (reflection + refraction + light highlight)
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

                # Slight per-sphere tint variation.
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

            # Slightly stronger tone mapping.
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
```
</details>

<details>
<summary>Transpiled code (C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin | Ruby)</summary>

- C++: [View full code](sample/cpp/16_glass_sculpture_chaos.cpp)
- Rust: [View full code](sample/rs/16_glass_sculpture_chaos.rs)
- C#: [View full code](sample/cs/16_glass_sculpture_chaos.cs)
- JavaScript: [View full code](sample/js/16_glass_sculpture_chaos.js)
- TypeScript: [View full code](sample/ts/16_glass_sculpture_chaos.ts)
- Go: [View full code](sample/go/16_glass_sculpture_chaos.go)
- Java: [View full code](sample/java/16_glass_sculpture_chaos.java)
- Swift: [View full code](sample/swift/16_glass_sculpture_chaos.swift)
- Kotlin: [View full code](sample/kotlin/16_glass_sculpture_chaos.kt)
- Ruby: [View full code](sample/ruby/16_glass_sculpture_chaos.rb)

</details>

## License

Apache License 2.0
