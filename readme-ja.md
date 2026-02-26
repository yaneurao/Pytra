# Pytraとは何？

<a href="readme.md">
  <img alt="Read in English" src="https://img.shields.io/badge/README-English-2563EB?style=flat-square">
</a>

Pytra は、Pythonのサブセットで書かれたプログラムを様々な言語に変換するためのトランスパイラ群です。

## 最新ニュース

> **2026-02-25 | v0.2.0 リリース**  
> バージョン 0.2.0 リリース、全言語について元ソースコードに近い形で出力されるようになりました。  

> **2026-02-23 | v0.1.0 リリース**  
> Pythonの元ソースコードに極めて近いスタイルで、より読みやすい C++ コードを生成できるようになりました。  

- 過去ニュース: [docs-ja/news/index.md](docs-ja/news/index.md)


## 特徴

Pytraの特徴

- Pythonから各言語への変換器
  - C++, C#, Rust, JavaScript, TypeScript, Go, Java, Swift, Kotlin に変換可能。
  - 元のソースコードに極めて近い形のまま変換

- C++で書くのと同等のコードをPythonで書けることが目標
  - intはデフォルトで 64-bit 符号付き整数
  - 動的な型付けなし

- シンプルな言語仕様
  - 基本的にPythonのサブセット
  - VS Code など既存ツールで開発できる
  - 多重継承を廃して、単純継承のみ

- 高い拡張性
  - トランスパイラ本体も Python で実装しており、拡張・改造しやすい構成
  - トランスパイラ自身のソースコードも本トランスパイラで他言語へ変換でき、セルフホスティングが可能

加えて、次の点も実運用上のメリットとして重視しています。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

⚠ Pythonで書いたプログラム丸ごとを移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。

## 実行速度の比較

Pythonで書かれた[サンプルコード](sample/readme-ja.md)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒）

|No.|内容|Python| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |マンデルブロ集合（PNG）|18.647|0.751|0.740|0.383|0.768|0.806|0.753|0.756|0.760|0.756|
|02 |球の簡易レイトレーサ（PNG）|6.890|0.185|0.155|0.918|0.277|0.288|0.256|0.260|0.289|0.258|
|03 |ジュリア集合（PNG）|22.770|0.810|0.768|1.468|1.210|1.127|1.126|1.136|1.125|1.151|
|04 |オービットトラップ Julia（PNG）|11.950|0.360|0.342|0.416|0.473|0.504|0.466|0.471|0.482|0.469|
|05 |マンデルブロズーム（GIF）|14.538|0.525|0.532|1.710|0.703|0.680|0.691|0.689|0.695|0.687|
|06 |ジュリア集合パラメータ掃引（GIF）|9.627|0.518|0.384|0.329|0.626|0.619|0.622|0.621|0.624|0.629|
|07 |ライフゲーム（GIF）|5.134|0.330|0.337|1.530|1.364|1.311|1.191|1.248|1.290|1.267|
|08 |ラングトンのアリ（GIF）|5.220|0.420|0.439|2.213|2.031|1.997|1.912|2.011|1.886|2.019|
|09 |炎シミュレーション（GIF）|10.895|0.569|0.612|6.566|2.374|2.290|2.368|2.265|2.306|2.358|
|10 |プラズマエフェクト（GIF）|6.194|0.643|0.527|2.646|1.444|1.886|1.397|1.414|1.444|1.319|
|11 |リサージュ粒子（GIF）|3.582|0.325|0.330|0.714|1.425|1.406|1.389|1.365|1.371|1.413|
|12 |ソート可視化（GIF）|3.864|0.307|0.331|0.680|1.341|1.343|1.309|1.348|1.328|1.306|
|13 |迷路生成ステップ（GIF）|3.402|0.273|0.277|1.037|1.038|1.035|0.985|1.025|0.997|0.987|
|14 |簡易レイマーチング（GIF）|2.670|0.150|0.149|0.606|0.489|0.573|0.490|0.513|0.503|0.492|
|15 |波干渉ループ（GIF）|2.631|0.288|0.237|1.196|0.616|0.794|0.609|0.614|0.629|0.612|
|16 |ガラス彫刻のカオス回転（GIF）|6.847|0.260|0.227|1.220|0.650|0.822|0.638|0.643|0.667|0.643|
|17 |モンテカルロ法で円周率近似（PNG）|0.293|0.002|0.002|0.010|0.046|0.045|0.047|0.048|0.047|0.048|
|18 |ミニ言語インタプリタ|2.037|0.335|0.386|0.735|0.446|0.446|0.405|0.417|0.423|0.417|

注記:
- 表の値は 2026-02-26 時点で `sample/py` 18件を現行トランスパイラ出力で再計測した実測値です（小数第3位丸め）。
- 計測プロトコルは fresh transpile・`warmup=1`・`repeat=5`・`elapsed_sec` の中央値採用（コンパイル時間は除外）です。
- 最新計測では `>1.5x` の乖離はありません（18件すべて `<=1.5x`）。
- Go/Java/Swift/Kotlin は現行実装で JS sidecar bridge 経由で実行されるため、値は bridge 実行経路の計測値です。
- 出力整合性は `sample/py` 18件について `cpp/rs/cs/js/ts/go/java/swift/kotlin` 全言語で一致を確認済みです（`tools/runtime_parity_check.py` の S3〜S7 検証ログ）。

![06_julia_parameter_sweep](sample/images/06_julia_parameter_sweep.gif)

<details>
<summary>サンプルコード : 06_julia_parameter_sweep.py</summary>

```python
# 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from pylib.tra.gif import save_gif


def julia_palette() -> bytes:
    # 先頭色は集合内部用に黒固定、残りは高彩度グラデーションを作る。
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
                # フレーム位相を少し加えて色が滑らかに流れるようにする。
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
    # 既知の見栄えが良い近傍を楕円軌道で巡回し、単調な白飛びを抑える。
    center_cr = -0.745
    center_ci = 0.186
    radius_cr = 0.12
    radius_ci = 0.10
    # GitHub上のサムネイルで暗く見えないよう、開始位置と色位相にオフセットを入れる。
    # 赤みが強い色域から始まるように調整する。
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
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin）</summary>

- C++: [View full code](sample/cpp/06_julia_parameter_sweep.cpp)
- Rust: [View full code](sample/rs/06_julia_parameter_sweep.rs)
- C#: [View full code](sample/cs/06_julia_parameter_sweep.cs)
- JavaScript: [View full code](sample/js/06_julia_parameter_sweep.js)
- TypeScript: [View full code](sample/ts/06_julia_parameter_sweep.ts)
- Go: [View full code](sample/go/06_julia_parameter_sweep.go)
- Java: [View full code](sample/java/06_julia_parameter_sweep.java)
- Swift: [View full code](sample/swift/06_julia_parameter_sweep.swift)
- Kotlin: [View full code](sample/kotlin/06_julia_parameter_sweep.kt)

</details>

<br/>

![16_glass_sculpture_chaos](sample/images/16_glass_sculpture_chaos.gif)

<details>
<summary>サンプルコード : 16_glass_sculpture_chaos.py</summary>

```python
# 16: ガラス彫刻のカオス回転をレイトレーシングで描き、GIF出力するサンプル。

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
```
</details>

<details>
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin）</summary>

- C++: [View full code](sample/cpp/16_glass_sculpture_chaos.cpp)
- Rust: [View full code](sample/rs/16_glass_sculpture_chaos.rs)
- C#: [View full code](sample/cs/16_glass_sculpture_chaos.cs)
- JavaScript: [View full code](sample/js/16_glass_sculpture_chaos.js)
- TypeScript: [View full code](sample/ts/16_glass_sculpture_chaos.ts)
- Go: [View full code](sample/go/16_glass_sculpture_chaos.go)
- Java: [View full code](sample/java/16_glass_sculpture_chaos.java)
- Swift: [View full code](sample/swift/16_glass_sculpture_chaos.swift)
- Kotlin: [View full code](sample/kotlin/16_glass_sculpture_chaos.kt)

</details>

## ドキュメント

利用時によく参照する順で、関連ドキュメントをまとめています。

- まず使い方を確認する: [使い方ガイド](docs-ja/how-to-use.md)
- 開発補助スクリプト一覧を確認する: [ツール一覧](docs-ja/spec/spec-tools.md)
- オプション設計（性能/互換性トレードオフ）を確認する: [オプション仕様](docs-ja/spec/spec-options.md)
- ランタイム配置と include 規約を確認する: [ランタイム仕様](docs-ja/spec/spec-runtime.md)
- 実装済み項目・未実装項目・対応予定なしを確認する: [実装状況メモ](docs-ja/plans/pytra-wip.md)
- `py2cpp` の機能対応（テスト根拠）を確認する: [py2cpp サポートマトリクス](docs-ja/language/cpp/spec-support.md)
- サンプル一覧と概要を確認する: [サンプルコード案内](sample/readme-ja.md)
- 仕様・制約・構成・運用ルールを確認する: [仕様書トップ](docs-ja/spec/index.md)
- 開発の動機と設計理念: [開発思想](docs-ja/spec/spec-philosophy.md)

## ライセンス

Apache License 2.0
