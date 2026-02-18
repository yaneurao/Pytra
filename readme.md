# Pytraとは何？

Pytra は、Pythonのサブセットで書かれたプログラムを様々な言語に変換するためのトランスパイラ群です。

## 特徴

Python から C++/Rust/C#/JavaScript/TypeScript/Go/Java/Swift/Kotlin への変換に対応しています。

変換元は Python のサブセットなので、元コードは通常の Python 環境でも実行できます。  
そのため、普段どおりの開発体験（補完やデバッグを含む）で実装しながら、必要に応じて各言語へ変換できます。

トランスパイラ本体も Python で実装しており、拡張・改造しやすい構成です。

さらに、トランスパイラ自身のソースコードも本トランスパイラで他言語へ変換できます。  
例えば C++ へ変換して実行し、変換処理を高速化するといった使い方も可能です。  
このように、**セルフホスティング可能**であることは、処理系依存の低減や、変換器自身の品質検証を継続しやすい点で大きなメリットです。

また、本トランスパイラは変換後の可読性を重視しており、元のソースコードの構造や意図（コメント・関数構成・制御フロー）をなるべく崩さずに対象言語へ変換することを特徴としています。  
この **変換元ソースコードに極めて近い出力** により、コードレビュー、差分確認、デバッグがしやすくなります。

加えて、次の点も実運用上のメリットとして重視しています。

- 1つの Python コードベースから複数言語へ展開できるため、仕様差分や重複実装を減らしやすい。
- Python 実行と各ターゲット実行を比較しやすく、性能改善（特に C++/Rust 化）を進めやすい。
- Python をいったん内部の中間表現（EAST）へ正規化してから各言語へ変換するため、段階的な機能拡張を行いやすい。
- Python 標準 `ast` への依存を廃しており、セルフホスティング（トランスパイラ自身を自分で変換）が可能。
- 変換対象の Python コードは標準 Python の文法を前提としているため、VS Code など既存ツールで開発しやすい。
- C++ へ変換した場合は、ネイティブコードに近い実行速度を狙える設計になっている。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

⚠ Pythonで書いたプログラム丸ごとを移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。



## 実行速度の比較

Pythonで書かれた[サンプルコード](docs/sample-code.md)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒）

|No.|内容|Python| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |マンデルブロ集合（PNG）|16.338|0.748|0.719|2.549|1.519|1.489|0.829|9.224|1.481|1.489|
|02 |球の簡易レイトレーサ（PNG）|5.300|0.176|0.155|0.865|0.436|0.460|0.413|6.554|0.441|0.439|
|03 |ジュリア集合（PNG）|13.320|0.808|0.675|3.395|1.816|1.834|1.118|3.983|1.731|1.782|
|04 |モンテカルロ法で円周率近似|0.327|0.007|0.197|0.601|2.118|2.153|0.360|3.145|2.153|2.154|
|05 |マンデルブロズーム（GIF）|14.615|0.533|0.539|2.694|1.193|1.243|0.623|3.016|1.256|1.229|
|06 |ジュリア集合パラメータ掃引（GIF）|9.706|0.377|0.387|1.929|0.981|0.997|0.503|3.708|1.002|0.996|
|07 |ライフゲーム（GIF）|13.576|0.793|0.722|3.272|2.750|2.949|1.682|4.727|2.808|2.853|
|08 |ラングトンのアリ（GIF）|7.469|0.498|0.453|2.233|1.946|2.145|0.967|2.004|2.205|2.049|
|09 |炎シミュレーション（GIF）|13.829|0.670|0.607|6.488|2.480|2.525|2.692|3.483|2.546|2.534|
|10 |プラズマエフェクト（GIF）|7.431|0.679|0.529|2.356|1.539|2.156|0.887|2.636|1.519|1.512|
|11 |リサージュ粒子（GIF）|5.214|0.374|0.343|0.754|1.535|1.598|0.439|0.759|1.576|1.594|
|12 |ソート可視化（GIF）|11.402|0.742|0.684|1.852|3.098|3.249|1.186|2.537|3.248|3.136|
|13 |迷路生成ステップ（GIF）|4.879|0.298|0.274|0.946|1.069|1.162|0.505|0.859|1.091|1.086|
|14 |簡易レイマーチング（GIF）|3.103|0.161|0.149|0.467|0.505|0.761|0.288|0.798|0.533|0.520|
|15 |ミニ言語インタプリタ |2.415|0.254|0.789|1.035|0.509|0.465|3.261|1.984|0.524|0.512|
|16 |ガラス彫刻のカオス回転（GIF）|7.352|0.258|0.231|1.289|0.940|1.105|3.014|4.025|0.977|0.991|

![06_julia_parameter_sweep](images/06_julia_parameter_sweep.gif)

<details>
<summary>サンプルコード : 06_julia_parameter_sweep.py</summary>

```python
# 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from pylib.gif import save_gif


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

![16_glass_sculpture_chaos](images/16_glass_sculpture_chaos.gif)

<details>
<summary>サンプルコード : 16_glass_sculpture_chaos.py</summary>

```python
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

- まず使い方を確認する: [docs/how-to-use.md](docs/how-to-use.md)
- 実装済み項目・未実装項目・対応予定なしを確認する: [docs/pytra-readme.md](docs/pytra-readme.md)
- サンプル一覧と概要を確認する: [docs/sample-code.md](docs/sample-code.md)
- 仕様・制約・構成・運用ルールを確認する: [docs/spec.md](docs/spec.md)
- 開発の動機と設計理念: [docs/philosophy.md](docs/philosophy.md)

## ライセンス

MIT License
