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

- 1つの Python コードベースから複数言語へ展開できるため、仕様差分や重複実装を減らせる。
- Python 実行と各ターゲット実行を比較しやすく、性能改善（特に C++/Rust 化）に繋げやすい。


## 開発動機

マルチプラットフォーム開発では、用途ごとに言語が分かれがちです。  
例えば、クライアントは C# や JavaScript、サーバーは Python、モバイルは Kotlin/Swift という構成が現実的に発生します。

この状況では、同じロジックを複数言語で繰り返し実装・保守することになり、コストと不整合のリスクが大きくなります。

「コアロジックを Python で書き、必要な言語へ変換できれば効率が上がる」という考えから、Pytra を開発しました。

また、素の Python だけでは性能が足りない場面もあるため、C++ や Rust などへ変換して高速化できることも重視しています。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

⚠ Pythonで書いたプログラム丸ごとを移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。


## 実行速度の比較

Pythonで書かれた[サンプルコード](docs/sample-code.md)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒）

|No.|内容|Python| C++ | Rust | C# | JS | TS | Go | Java | Swift | Kotlin |
|-|-|-:|-:|-:|-:|-:|-:|-:|-:|-:|-:|
|01 |マンデルブロ集合（PNG）|16.175|0.754|0.719|2.549|1.519|1.489|0.829|9.224|1.481|1.489|
|02 |球の簡易レイトレーサ（PNG）|5.132|0.108|0.155|0.865|0.436|0.460|0.413|6.554|0.441|0.439|
|03 |ジュリア集合（PNG）|13.578|0.808|0.675|3.395|1.816|1.834|1.118|3.983|1.731|1.782|
|04 |モンテカルロ法で円周率近似|10.921|0.161|0.197|0.601|2.118|2.153|0.360|3.145|2.153|2.154|
|05 |マンデルブロズーム（GIF）|13.802|0.544|0.539|2.694|1.193|1.243|0.623|3.016|1.256|1.229|
|06 |ジュリア集合パラメータ掃引（GIF）|9.825|0.386|0.387|1.929|0.981|0.997|0.503|3.708|1.002|0.996|
|07 |ライフゲーム（GIF）|13.645|0.692|0.722|3.272|2.750|2.949|1.682|4.727|2.808|2.853|
|08 |ラングトンのアリ（GIF）|7.431|0.471|0.453|2.233|1.946|2.145|0.967|2.004|2.205|2.049|
|09 |炎シミュレーション（GIF）|13.649|0.625|0.607|6.488|2.480|2.525|2.692|3.483|2.546|2.534|
|10 |プラズマエフェクト（GIF）|7.640|0.527|0.529|2.356|1.539|2.156|0.887|2.636|1.519|1.512|
|11 |リサージュ粒子（GIF）|5.250|0.350|0.343|0.754|1.535|1.598|0.439|0.759|1.576|1.594|
|12 |ソート可視化（GIF）|11.451|0.648|0.684|1.852|3.098|3.249|1.186|2.537|3.248|3.136|
|13 |迷路生成ステップ（GIF）|4.716|0.283|0.274|0.946|1.069|1.162|0.505|0.859|1.091|1.086|
|14 |簡易レイマーチング（GIF）|2.666|0.123|0.149|0.467|0.505|0.761|0.288|0.798|0.533|0.520|
|15 |ミニ言語インタプリタ |2.207|0.600|0.789|1.035|0.509|0.465|3.261|1.984|0.524|0.512|
|16 |ガラス彫刻のカオス回転（GIF）|7.114|0.205|0.231|1.289|0.940|1.105|3.014|4.025|0.977|0.991|

![06_julia_parameter_sweep](images/06_julia_parameter_sweep.gif)

<details>
<summary>サンプルコード : 06_julia_parameter_sweep.py</summary>

```python
# 06: ジュリア集合のパラメータを回してGIF出力するサンプル。

from __future__ import annotations

import math
from time import perf_counter

from py_module.gif_helper import save_gif


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
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin）: 06_julia_parameter_sweep</summary>

<details>
<summary>C++への変換例 : 06_julia_parameter_sweep.cpp</summary>

```cpp
#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

vector<uint8_t> julia_palette()
{
    vector<uint8_t> palette = py_bytearray((256 * 3));
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    auto __pytra_range_start_1 = 1;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        double t = py_div((i - 1), 254.0);
        long long r = static_cast<long long>((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)));
        long long g = static_cast<long long>((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)));
        long long b = static_cast<long long>((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)));
        palette[((i * 3) + 0)] = r;
        palette[((i * 3) + 1)] = g;
        palette[((i * 3) + 2)] = b;
    }
    return py_bytes(palette);
}

vector<uint8_t> render_frame(long long width, long long height, double cr, double ci, long long max_iter, long long phase)
{
    vector<uint8_t> frame = py_bytearray((width * height));
    long long idx = 0;
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = height;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
    {
        double zy0 = ((-1.2) + (2.4 * py_div(y, (height - 1))));
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = width;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
        {
            double zx = ((-1.8) + (3.6 * py_div(x, (width - 1))));
            auto zy = zy0;
            long long i = 0;
            while ((i < max_iter))
            {
                auto zx2 = (zx * zx);
                auto zy2 = (zy * zy);
                if (((zx2 + zy2) > 4.0))
                {
                    break;
                }
                zy = (((2.0 * zx) * zy) + ci);
                zx = ((zx2 - zy2) + cr);
                i = (i + 1);
            }
            if ((i >= max_iter))
            {
                frame[idx] = 0;
            }
            else
            {
                long long color_index = (1 + ((py_floordiv((i * 224), max_iter) + phase) % 255));
                frame[idx] = color_index;
            }
            idx = (idx + 1);
        }
    }
    return py_bytes(frame);
}

void run_06_julia_parameter_sweep()
{
    long long width = 320;
    long long height = 240;
    long long frames_n = 72;
    long long max_iter = 180;
    string out_path = "sample/out/06_julia_parameter_sweep.gif";
    auto start = perf_counter();
    vector<vector<uint8_t>> frames = {};
    double center_cr = (-0.745);
    double center_ci = 0.186;
    double radius_cr = 0.12;
    double radius_ci = 0.1;
    long long start_offset = 20;
    long long phase_offset = 180;
    auto __pytra_range_start_10 = 0;
    auto __pytra_range_stop_11 = frames_n;
    auto __pytra_range_step_12 = 1;
    if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
    {
        double t = py_div(((i + start_offset) % frames_n), frames_n);
        double angle = ((2.0 * pycs::cpp_module::math::pi) * t);
        auto cr = (center_cr + (radius_cr * pycs::cpp_module::math::cos(angle)));
        auto ci = (center_ci + (radius_ci * pycs::cpp_module::math::sin(angle)));
        long long phase = ((phase_offset + (i * 5)) % 255);
        frames.push_back(render_frame(width, height, cr, ci, max_iter, phase));
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_06_julia_parameter_sweep();
    return 0;
}
```
</details>

<details>
<summary>Rustへの変換例 : 06_julia_parameter_sweep.rs</summary>

```rust
#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn julia_palette() -> Vec<u8> {
    let mut palette = vec![0u8; (((256) * (3))) as usize];
    (palette)[0 as usize] = (0) as u8;
    (palette)[1 as usize] = (0) as u8;
    (palette)[2 as usize] = (0) as u8;
    for i in (1)..(256) {
        let mut t = ((( ((i) - (1)) ) as f64) / (( 254.0 ) as f64));
        let mut r = ((((255.0) * (((((((((9.0) * (((1.0) - (t))))) * (t))) * (t))) * (t))))) as i64);
        let mut g = ((((255.0) * (((((((((15.0) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))) * (t))))) as i64);
        let mut b = ((((255.0) * (((((((((8.5) * (((1.0) - (t))))) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))))) as i64);
        (palette)[((((i) * (3))) + (0)) as usize] = (r) as u8;
        (palette)[((((i) * (3))) + (1)) as usize] = (g) as u8;
        (palette)[((((i) * (3))) + (2)) as usize] = (b) as u8;
    }
    return (palette).clone();
}

fn render_frame(mut width: i64, mut height: i64, mut cr: f64, mut ci: f64, mut max_iter: i64, mut phase: i64) -> Vec<u8> {
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    let mut idx = 0;
    for y in (0)..(height) {
        let mut zy0 = (((-1.2)) + (((2.4) * (((( y ) as f64) / (( ((height) - (1)) ) as f64))))));
        for x in (0)..(width) {
            let mut zx = (((-1.8)) + (((3.6) * (((( x ) as f64) / (( ((width) - (1)) ) as f64))))));
            let mut zy = zy0;
            let mut i = 0;
            while py_bool(&(((i) < (max_iter)))) {
                let mut zx2 = ((zx) * (zx));
                let mut zy2 = ((zy) * (zy));
                if py_bool(&(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (ci));
                zx = ((((zx2) - (zy2))) + (cr));
                i = i + 1;
            }
            if py_bool(&(((i) >= (max_iter)))) {
                (frame)[idx as usize] = (0) as u8;
            } else {
                let mut color_index = ((1) + (((((((((i) * (224))) / (max_iter))) + (phase))) % (255))));
                (frame)[idx as usize] = (color_index) as u8;
            }
            idx = idx + 1;
        }
    }
    return (frame).clone();
}

fn run_06_julia_parameter_sweep() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frames_n = 72;
    let mut max_iter = 180;
    let mut out_path = "sample/out/06_julia_parameter_sweep.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    let mut center_cr = (-0.745);
    let mut center_ci = 0.186;
    let mut radius_cr = 0.12;
    let mut radius_ci = 0.1;
    let mut start_offset = 20;
    let mut phase_offset = 180;
    for i in (0)..(frames_n) {
        let mut t = ((( ((((i) + (start_offset))) % (frames_n)) ) as f64) / (( frames_n ) as f64));
        let mut angle = ((((2.0) * (std::f64::consts::PI))) * (t));
        let mut cr = ((center_cr) + (((radius_cr) * (math_cos(((angle) as f64))))));
        let mut ci = ((center_ci) + (((radius_ci) * (math_sin(((angle) as f64))))));
        let mut phase = ((((phase_offset) + (((i) * (5))))) % (255));
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    py_save_gif(&(out_path), width, height, &(frames), &(julia_palette()), 8, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_06_julia_parameter_sweep();
}
```
</details>

<details>
<summary>C#への変換例 : 06_julia_parameter_sweep.cs</summary>

```csharp
using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> julia_palette()
    {
        var palette = Pytra.CsModule.py_runtime.py_bytearray((256L * 3L));
        Pytra.CsModule.py_runtime.py_set(palette, 0L, 0L);
        Pytra.CsModule.py_runtime.py_set(palette, 1L, 0L);
        Pytra.CsModule.py_runtime.py_set(palette, 2L, 0L);
        var __pytra_range_start_1 = 1L;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var t = ((double)((i - 1L)) / (double)(254.0));
            var r = (long)((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)));
            var g = (long)((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)));
            var b = (long)((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)));
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 0L), r);
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 1L), g);
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 2L), b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(palette);
    }

    public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter, long phase)
    {
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
        long idx = 0L;
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = height;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            var zy0 = ((-1.2) + (2.4 * ((double)(y) / (double)((height - 1L)))));
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = width;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                var zx = ((-1.8) + (3.6 * ((double)(x) / (double)((width - 1L)))));
                var zy = zy0;
                long i = 0L;
                while (Pytra.CsModule.py_runtime.py_bool((i < max_iter)))
                {
                    var zx2 = (zx * zx);
                    var zy2 = (zy * zy);
                    if (Pytra.CsModule.py_runtime.py_bool(((zx2 + zy2) > 4.0)))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + ci);
                    zx = ((zx2 - zy2) + cr);
                    i = (i + 1L);
                }
                if (Pytra.CsModule.py_runtime.py_bool((i >= max_iter)))
                {
                    Pytra.CsModule.py_runtime.py_set(frame, idx, 0L);
                }
                else
                {
                    var color_index = (1L + (((long)Math.Floor(((i * 224L)) / (double)(max_iter)) + phase) % 255L));
                    Pytra.CsModule.py_runtime.py_set(frame, idx, color_index);
                }
                idx = (idx + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_06_julia_parameter_sweep()
    {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        long max_iter = 180L;
        string out_path = "sample/out/06_julia_parameter_sweep.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var center_cr = (-0.745);
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.1;
        long start_offset = 20L;
        long phase_offset = 180L;
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = frames_n;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
        {
            var t = ((double)(((i + start_offset) % frames_n)) / (double)(frames_n));
            var angle = ((2.0 * Math.PI) * t);
            var cr = (center_cr + (radius_cr * Math.Cos(angle)));
            var ci = (center_ci + (radius_ci * Math.Sin(angle)));
            var phase = ((phase_offset + (i * 5L)) % 255L);
            Pytra.CsModule.py_runtime.py_append(frames, render_frame(width, height, cr, ci, max_iter, phase));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, julia_palette(), delay_cs: 8L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_06_julia_parameter_sweep();
    }
}
```
</details>

<details>
<summary>JavaScriptへの変換例 : 06_julia_parameter_sweep.js</summary>

```javascript
// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/js_module/math.js');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function julia_palette() {
    let palette = pyBytearray(((256) * (3)));
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    let i;
    for (let __pytra_i_1 = 1; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let t = ((((i) - (1))) / (254.0));
        let r = Math.trunc(Number(((255.0) * (((((((((9.0) * (((1.0) - (t))))) * (t))) * (t))) * (t))))));
        let g = Math.trunc(Number(((255.0) * (((((((((15.0) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))) * (t))))));
        let b = Math.trunc(Number(((255.0) * (((((((((8.5) * (((1.0) - (t))))) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))))));
        palette[((((i) * (3))) + (0))] = r;
        palette[((((i) * (3))) + (1))] = g;
        palette[((((i) * (3))) + (2))] = b;
    }
    return pyBytes(palette);
}
function render_frame(width, height, cr, ci, max_iter, phase) {
    let frame = pyBytearray(((width) * (height)));
    let idx = 0;
    let y;
    for (let __pytra_i_2 = 0; __pytra_i_2 < height; __pytra_i_2 += 1) {
        y = __pytra_i_2;
        let zy0 = (((-(1.2))) + (((2.4) * (((y) / (((height) - (1))))))));
        let x;
        for (let __pytra_i_3 = 0; __pytra_i_3 < width; __pytra_i_3 += 1) {
            x = __pytra_i_3;
            let zx = (((-(1.8))) + (((3.6) * (((x) / (((width) - (1))))))));
            let zy = zy0;
            let i = 0;
            while (pyBool(((i) < (max_iter)))) {
                let zx2 = ((zx) * (zx));
                let zy2 = ((zy) * (zy));
                if (pyBool(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (ci));
                zx = ((((zx2) - (zy2))) + (cr));
                i = i + 1;
            }
            if (pyBool(((i) >= (max_iter)))) {
                frame[idx] = 0;
            } else {
                let color_index = ((1) + (pyMod(((pyFloorDiv(((i) * (224)), max_iter)) + (phase)), 255)));
                frame[idx] = color_index;
            }
            idx = idx + 1;
        }
    }
    return pyBytes(frame);
}
function run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = 'sample/out/06_julia_parameter_sweep.gif';
    let start = perf_counter();
    let frames = [];
    let center_cr = (-(0.745));
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.1;
    let start_offset = 20;
    let phase_offset = 180;
    let i;
    for (let __pytra_i_4 = 0; __pytra_i_4 < frames_n; __pytra_i_4 += 1) {
        i = __pytra_i_4;
        let t = ((pyMod(((i) + (start_offset)), frames_n)) / (frames_n));
        let angle = ((((2.0) * (math.pi))) * (t));
        let cr = ((center_cr) + (((radius_cr) * (math.cos(angle)))));
        let ci = ((center_ci) + (((radius_ci) * (math.sin(angle)))));
        let phase = pyMod(((phase_offset) + (((i) * (5)))), 255);
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_06_julia_parameter_sweep();
```
</details>

<details>
<summary>TypeScriptへの変換例 : 06_julia_parameter_sweep.ts</summary>

```typescript
// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/ts_module/math.ts');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/ts_module/gif_helper.ts');

function julia_palette() {
    let palette = pyBytearray(((256) * (3)));
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    let i;
    for (let __pytra_i_1 = 1; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let t = ((((i) - (1))) / (254.0));
        let r = Math.trunc(Number(((255.0) * (((((((((9.0) * (((1.0) - (t))))) * (t))) * (t))) * (t))))));
        let g = Math.trunc(Number(((255.0) * (((((((((15.0) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))) * (t))))));
        let b = Math.trunc(Number(((255.0) * (((((((((8.5) * (((1.0) - (t))))) * (((1.0) - (t))))) * (((1.0) - (t))))) * (t))))));
        palette[((((i) * (3))) + (0))] = r;
        palette[((((i) * (3))) + (1))] = g;
        palette[((((i) * (3))) + (2))] = b;
    }
    return pyBytes(palette);
}
function render_frame(width, height, cr, ci, max_iter, phase) {
    let frame = pyBytearray(((width) * (height)));
    let idx = 0;
    let y;
    for (let __pytra_i_2 = 0; __pytra_i_2 < height; __pytra_i_2 += 1) {
        y = __pytra_i_2;
        let zy0 = (((-(1.2))) + (((2.4) * (((y) / (((height) - (1))))))));
        let x;
        for (let __pytra_i_3 = 0; __pytra_i_3 < width; __pytra_i_3 += 1) {
            x = __pytra_i_3;
            let zx = (((-(1.8))) + (((3.6) * (((x) / (((width) - (1))))))));
            let zy = zy0;
            let i = 0;
            while (pyBool(((i) < (max_iter)))) {
                let zx2 = ((zx) * (zx));
                let zy2 = ((zy) * (zy));
                if (pyBool(((((zx2) + (zy2))) > (4.0)))) {
                    break;
                }
                zy = ((((((2.0) * (zx))) * (zy))) + (ci));
                zx = ((((zx2) - (zy2))) + (cr));
                i = i + 1;
            }
            if (pyBool(((i) >= (max_iter)))) {
                frame[idx] = 0;
            } else {
                let color_index = ((1) + (pyMod(((pyFloorDiv(((i) * (224)), max_iter)) + (phase)), 255)));
                frame[idx] = color_index;
            }
            idx = idx + 1;
        }
    }
    return pyBytes(frame);
}
function run_06_julia_parameter_sweep() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let max_iter = 180;
    let out_path = 'sample/out/06_julia_parameter_sweep.gif';
    let start = perf_counter();
    let frames = [];
    let center_cr = (-(0.745));
    let center_ci = 0.186;
    let radius_cr = 0.12;
    let radius_ci = 0.1;
    let start_offset = 20;
    let phase_offset = 180;
    let i;
    for (let __pytra_i_4 = 0; __pytra_i_4 < frames_n; __pytra_i_4 += 1) {
        i = __pytra_i_4;
        let t = ((pyMod(((i) + (start_offset)), frames_n)) / (frames_n));
        let angle = ((((2.0) * (math.pi))) * (t));
        let cr = ((center_cr) + (((radius_cr) * (math.cos(angle)))));
        let ci = ((center_ci) + (((radius_ci) * (math.sin(angle)))));
        let phase = pyMod(((phase_offset) + (((i) * (5)))), 255);
        frames.push(render_frame(width, height, cr, ci, max_iter, phase));
    }
    save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_06_julia_parameter_sweep();
```
</details>

<details>
<summary>Goへの変換例 : 06_julia_parameter_sweep.go</summary>

```go
// このファイルは自動生成です（Python -> Go native mode）。

// Go ネイティブ変換向け Python 互換ランタイム補助。

package main

import (
    "bytes"
    "compress/zlib"
    "fmt"
    "hash/crc32"
    "math"
    "os"
    "strconv"
    "strings"
    "time"
)

func pyToString(v any) string {
    switch x := v.(type) {
    case nil:
        return "None"
    case bool:
        if x {
            return "True"
        }
        return "False"
    case string:
        return x
    case int:
        return strconv.Itoa(x)
    case int64:
        return strconv.FormatInt(x, 10)
    case float64:
        return strconv.FormatFloat(x, 'f', -1, 64)
    case []any:
        parts := make([]string, 0, len(x))
        for _, it := range x {
            parts = append(parts, pyToString(it))
        }
        return "[" + strings.Join(parts, ", ") + "]"
    case map[any]any:
        parts := make([]string, 0, len(x))
        for k, v := range x {
            parts = append(parts, pyToString(k)+": "+pyToString(v))
        }
        return "{" + strings.Join(parts, ", ") + "}"
    default:
        return fmt.Sprint(x)
    }
}

func pyPrint(args ...any) {
    parts := make([]string, 0, len(args))
    for _, a := range args {
        parts = append(parts, pyToString(a))
    }
    fmt.Println(strings.Join(parts, " "))
}

func pyBool(v any) bool {
    switch x := v.(type) {
    case nil:
        return false
    case bool:
        return x
    case int:
        return x != 0
    case int64:
        return x != 0
    case float64:
        return x != 0.0
    case string:
        return x != ""
    case []any:
        return len(x) > 0
    case []byte:
        return len(x) > 0
    case map[any]any:
        return len(x) > 0
    default:
        return true
    }
}

func pyLen(v any) int {
    switch x := v.(type) {
    case string:
        return len([]rune(x))
    case []any:
        return len(x)
    case []byte:
        return len(x)
    case map[any]any:
        return len(x)
    default:
        panic("len() unsupported type")
    }
}

func pyRange(start, stop, step int) []any {
    if step == 0 {
        panic("range() step must not be zero")
    }
    out := []any{}
    if step > 0 {
        for i := start; i < stop; i += step {
            out = append(out, i)
        }
    } else {
        for i := start; i > stop; i += step {
            out = append(out, i)
        }
    }
    return out
}

func pyToFloat(v any) float64 {
    switch x := v.(type) {
    case int:
        return float64(x)
    case int64:
        return float64(x)
    case float64:
        return x
    case bool:
        if x {
            return 1.0
        }
        return 0.0
    default:
        panic("cannot convert to float")
    }
}

func pyToInt(v any) int {
    switch x := v.(type) {
    case int:
        return x
    case int64:
        return int(x)
    case float64:
        return int(math.Trunc(x))
    case bool:
        if x {
            return 1
        }
        return 0
    default:
        panic("cannot convert to int")
    }
}

func pyAdd(a, b any) any {
    if sa, ok := a.(string); ok {
        return sa + pyToString(b)
    }
    if sb, ok := b.(string); ok {
        return pyToString(a) + sb
    }
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) + pyToInt(b)
    }
    return pyToFloat(a) + pyToFloat(b)
}
func pySub(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) - pyToInt(b)
    }
    return pyToFloat(a) - pyToFloat(b)
}
func pyMul(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) * pyToInt(b)
    }
    return pyToFloat(a) * pyToFloat(b)
}
func pyDiv(a, b any) any { return pyToFloat(a) / pyToFloat(b) }
func pyFloorDiv(a, b any) any { return int(math.Floor(pyToFloat(a) / pyToFloat(b))) }
func pyMod(a, b any) any {
    ai := pyToInt(a)
    bi := pyToInt(b)
    r := ai % bi
    if r != 0 && ((r > 0) != (bi > 0)) {
        r += bi
    }
    return r
}
func pyMin(values ...any) any {
    if len(values) == 0 {
        panic("min() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi < ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf < af {
            out = bf
        }
    }
    return out
}
func pyMax(values ...any) any {
    if len(values) == 0 {
        panic("max() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi > ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf > af {
            out = bf
        }
    }
    return out
}
func pyLShift(a, b any) any { return pyToInt(a) << uint(pyToInt(b)) }
func pyRShift(a, b any) any { return pyToInt(a) >> uint(pyToInt(b)) }
func pyBitAnd(a, b any) any { return pyToInt(a) & pyToInt(b) }
func pyBitOr(a, b any) any  { return pyToInt(a) | pyToInt(b) }
func pyBitXor(a, b any) any { return pyToInt(a) ^ pyToInt(b) }
func pyNeg(a any) any {
    if _, ok := a.(int); ok {
        return -pyToInt(a)
    }
    return -pyToFloat(a)
}

func pyEq(a, b any) bool { return pyToString(a) == pyToString(b) }
func pyNe(a, b any) bool { return !pyEq(a, b) }
func pyLt(a, b any) bool { return pyToFloat(a) < pyToFloat(b) }
func pyLe(a, b any) bool { return pyToFloat(a) <= pyToFloat(b) }
func pyGt(a, b any) bool { return pyToFloat(a) > pyToFloat(b) }
func pyGe(a, b any) bool { return pyToFloat(a) >= pyToFloat(b) }

func pyIn(item, container any) bool {
    switch c := container.(type) {
    case string:
        return strings.Contains(c, pyToString(item))
    case []any:
        for _, v := range c {
            if pyEq(v, item) {
                return true
            }
        }
        return false
    case map[any]any:
        _, ok := c[item]
        return ok
    default:
        return false
    }
}

func pyIter(value any) []any {
    switch v := value.(type) {
    case []any:
        return v
    case []byte:
        out := make([]any, 0, len(v))
        for _, b := range v {
            out = append(out, int(b))
        }
        return out
    case string:
        out := []any{}
        for _, ch := range []rune(v) {
            out = append(out, string(ch))
        }
        return out
    case map[any]any:
        out := []any{}
        for k := range v {
            out = append(out, k)
        }
        return out
    default:
        panic("iter unsupported")
    }
}

func pyTernary(cond bool, a any, b any) any {
    if cond {
        return a
    }
    return b
}

func pyListFromIter(value any) any {
    it := pyIter(value)
    out := make([]any, len(it))
    copy(out, it)
    return out
}

func pySlice(value any, start any, end any) any {
    s := 0
    e := 0
    switch v := value.(type) {
    case string:
        r := []rune(v)
        n := len(r)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        return string(r[s:e])
    case []any:
        n := len(v)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        out := make([]any, e-s)
        copy(out, v[s:e])
        return out
    default:
        panic("slice unsupported")
    }
}

func pyGet(value any, key any) any {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return v[i]
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return int(v[i])
    case map[any]any:
        return v[key]
    case string:
        r := []rune(v)
        i := pyToInt(key)
        if i < 0 {
            i += len(r)
        }
        return string(r[i])
    default:
        panic("subscript unsupported")
    }
}

func pySet(value any, key any, newValue any) {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = newValue
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = byte(pyToInt(newValue))
    case map[any]any:
        v[key] = newValue
    default:
        panic("setitem unsupported")
    }
}

func pyPop(lst *any, idx any) any {
    arr := (*lst).([]any)
    n := len(arr)
    i := n - 1
    if idx != nil {
        i = pyToInt(idx)
        if i < 0 {
            i += n
        }
    }
    val := arr[i]
    arr = append(arr[:i], arr[i+1:]...)
    *lst = arr
    return val
}

func pyPopAt(container any, key any, idx any) any {
    lst := pyGet(container, key)
    val := pyPop(&lst, idx)
    pySet(container, key, lst)
    return val
}

func pyOrd(v any) any {
    s := pyToString(v)
    r := []rune(s)
    return int(r[0])
}

func pyChr(v any) any { return string(rune(pyToInt(v))) }

func pyBytearray(size any) any {
    if size == nil {
        return []byte{}
    }
    n := pyToInt(size)
    out := make([]byte, n)
    return out
}

func pyBytes(v any) any { return v }

func pyAppend(seq any, value any) any {
    switch s := seq.(type) {
    case []any:
        return append(s, value)
    case []byte:
        return append(s, byte(pyToInt(value)))
    default:
        panic("append unsupported type")
    }
}

func pyIsDigit(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if ch < '0' || ch > '9' {
            return false
        }
    }
    return true
}

func pyIsAlpha(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
            return false
        }
    }
    return true
}

func pyTryCatch(body func() any, handler func(any) any, finalizer func()) (ret any) {
    defer finalizer()
    defer func() {
        if r := recover(); r != nil {
            ret = handler(r)
        }
    }()
    ret = body()
    return
}

// -------- time/math helper --------

func pyPerfCounter() any {
    return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func pyMathSqrt(v any) any { return math.Sqrt(pyToFloat(v)) }
func pyMathSin(v any) any  { return math.Sin(pyToFloat(v)) }
func pyMathCos(v any) any  { return math.Cos(pyToFloat(v)) }
func pyMathExp(v any) any  { return math.Exp(pyToFloat(v)) }
func pyMathFloor(v any) any { return float64(math.Floor(pyToFloat(v))) }
func pyMathPi() any        { return math.Pi }

// -------- png/gif helper --------

func pyToBytes(v any) []byte {
    switch x := v.(type) {
    case []byte:
        out := make([]byte, len(x))
        copy(out, x)
        return out
    case []any:
        out := make([]byte, len(x))
        for i, e := range x {
            out[i] = byte(pyToInt(e))
        }
        return out
    case string:
        return []byte(x)
    default:
        panic("cannot convert to bytes")
    }
}

func pyChunk(chunkType []byte, data []byte) []byte {
    var out bytes.Buffer
    n := uint32(len(data))
    out.Write([]byte{byte(n >> 24), byte(n >> 16), byte(n >> 8), byte(n)})
    out.Write(chunkType)
    out.Write(data)
    crc := crc32.ChecksumIEEE(append(append([]byte{}, chunkType...), data...))
    out.Write([]byte{byte(crc >> 24), byte(crc >> 16), byte(crc >> 8), byte(crc)})
    return out.Bytes()
}

func pyWriteRGBPNG(path any, width any, height any, pixels any) {
    w := pyToInt(width)
    h := pyToInt(height)
    raw := pyToBytes(pixels)
    expected := w * h * 3
    if len(raw) != expected {
        panic("pixels length mismatch")
    }

    scan := make([]byte, 0, h*(1+w*3))
    rowBytes := w * 3
    for y := 0; y < h; y++ {
        scan = append(scan, 0)
        start := y * rowBytes
        end := start + rowBytes
        scan = append(scan, raw[start:end]...)
    }

    var zbuf bytes.Buffer
    zw, _ := zlib.NewWriterLevel(&zbuf, 6)
    _, _ = zw.Write(scan)
    _ = zw.Close()
    idat := zbuf.Bytes()

    ihdr := []byte{
        byte(uint32(w) >> 24), byte(uint32(w) >> 16), byte(uint32(w) >> 8), byte(uint32(w)),
        byte(uint32(h) >> 24), byte(uint32(h) >> 16), byte(uint32(h) >> 8), byte(uint32(h)),
        8, 2, 0, 0, 0,
    }

    var png bytes.Buffer
    png.Write([]byte{0x89, 'P', 'N', 'G', '
', '
', 0x1a, '
'})
    png.Write(pyChunk([]byte("IHDR"), ihdr))
    png.Write(pyChunk([]byte("IDAT"), idat))
    png.Write(pyChunk([]byte("IEND"), []byte{}))

    _ = os.WriteFile(pyToString(path), png.Bytes(), 0o644)
}

func pyLzwEncode(data []byte, minCodeSize int) []byte {
    if len(data) == 0 {
        return []byte{}
    }
    clearCode := 1 << minCodeSize
    endCode := clearCode + 1
    codeSize := minCodeSize + 1
    out := []byte{}
    bitBuffer := 0
    bitCount := 0

    emit := func(code int) {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        for bitCount >= 8 {
            out = append(out, byte(bitBuffer&0xff))
            bitBuffer >>= 8
            bitCount -= 8
        }
    }

    emit(clearCode)
    for _, v := range data {
        emit(int(v))
        emit(clearCode)
    }
    emit(endCode)
    if bitCount > 0 {
        out = append(out, byte(bitBuffer&0xff))
    }
    return out
}

func pyGrayscalePalette() any {
    p := make([]byte, 0, 256*3)
    for i := 0; i < 256; i++ {
        p = append(p, byte(i), byte(i), byte(i))
    }
    return p
}

func pySaveGIF(path any, width any, height any, frames any, palette any, delayCS any, loop any) {
    w := pyToInt(width)
    h := pyToInt(height)
    frameBytes := w * h
    pal := pyToBytes(palette)
    if len(pal) != 256*3 {
        panic("palette must be 256*3 bytes")
    }
    dcs := pyToInt(delayCS)
    lp := pyToInt(loop)

    frs := pyIter(frames)
    out := []byte{}
    out = append(out, []byte("GIF89a")...)
    out = append(out, byte(w), byte(w>>8), byte(h), byte(h>>8))
    out = append(out, 0xF7, 0, 0)
    out = append(out, pal...)

    out = append(out, 0x21, 0xFF, 0x0B)
    out = append(out, []byte("NETSCAPE2.0")...)
    out = append(out, 0x03, 0x01, byte(lp), byte(lp>>8), 0x00)

    for _, frAny := range frs {
        fr := pyToBytes(frAny)
        if len(fr) != frameBytes {
            panic("frame size mismatch")
        }
        out = append(out, 0x21, 0xF9, 0x04, 0x00, byte(dcs), byte(dcs>>8), 0x00, 0x00)
        out = append(out, 0x2C, 0, 0, 0, 0, byte(w), byte(w>>8), byte(h), byte(h>>8), 0x00)
        out = append(out, 0x08)
        compressed := pyLzwEncode(fr, 8)
        pos := 0
        for pos < len(compressed) {
            ln := len(compressed) - pos
            if ln > 255 {
                ln = 255
            }
            out = append(out, byte(ln))
            out = append(out, compressed[pos:pos+ln]...)
            pos += ln
        }
        out = append(out, 0x00)
    }
    out = append(out, 0x3B)
    _ = os.WriteFile(pyToString(path), out, 0o644)
}

func julia_palette() any {
    var palette any = pyBytearray((256 * 3))
    _ = palette
    pySet(palette, 0, 0)
    pySet(palette, 1, 0)
    pySet(palette, 2, 0)
    __pytra_range_start_1 := pyToInt(1)
    __pytra_range_stop_2 := pyToInt(256)
    __pytra_range_step_3 := pyToInt(1)
    if __pytra_range_step_3 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_4 := __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3 {
        i = __pytra_i_4
        var t float64 = (float64((i - 1)) / 254.0)
        _ = t
        var r int = pyToInt((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)))
        _ = r
        var g int = pyToInt((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)))
        _ = g
        var b int = pyToInt((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)))
        _ = b
        pySet(palette, ((i * 3) + 0), r)
        pySet(palette, ((i * 3) + 1), g)
        pySet(palette, ((i * 3) + 2), b)
    }
    return pyBytes(palette)
}

func render_frame(width int, height int, cr float64, ci float64, max_iter int, phase int) any {
    var frame any = pyBytearray((width * height))
    _ = frame
    var idx int = 0
    _ = idx
    __pytra_range_start_5 := pyToInt(0)
    __pytra_range_stop_6 := pyToInt(height)
    __pytra_range_step_7 := pyToInt(1)
    if __pytra_range_step_7 == 0 { panic("range() step must not be zero") }
    var y int = 0
    _ = y
    for __pytra_i_8 := __pytra_range_start_5; (__pytra_range_step_7 > 0 && __pytra_i_8 < __pytra_range_stop_6) || (__pytra_range_step_7 < 0 && __pytra_i_8 > __pytra_range_stop_6); __pytra_i_8 += __pytra_range_step_7 {
        y = __pytra_i_8
        var zy0 float64 = ((-1.2) + (2.4 * (float64(y) / float64((height - 1)))))
        _ = zy0
        __pytra_range_start_9 := pyToInt(0)
        __pytra_range_stop_10 := pyToInt(width)
        __pytra_range_step_11 := pyToInt(1)
        if __pytra_range_step_11 == 0 { panic("range() step must not be zero") }
        var x int = 0
        _ = x
        for __pytra_i_12 := __pytra_range_start_9; (__pytra_range_step_11 > 0 && __pytra_i_12 < __pytra_range_stop_10) || (__pytra_range_step_11 < 0 && __pytra_i_12 > __pytra_range_stop_10); __pytra_i_12 += __pytra_range_step_11 {
            x = __pytra_i_12
            var zx float64 = ((-1.8) + (3.6 * (float64(x) / float64((width - 1)))))
            _ = zx
            var zy float64 = zy0
            _ = zy
            var i int = 0
            _ = i
            for pyBool((i < max_iter)) {
                var zx2 float64 = (zx * zx)
                _ = zx2
                var zy2 float64 = (zy * zy)
                _ = zy2
                if (pyBool(((zx2 + zy2) > 4.0))) {
                    break
                }
                zy = (((2.0 * zx) * zy) + ci)
                zx = ((zx2 - zy2) + cr)
                i = (i + 1)
            }
            if (pyBool((i >= max_iter))) {
                pySet(frame, idx, 0)
            } else {
                var color_index int = (1 + ((((i * 224) / max_iter) + phase) % 255))
                _ = color_index
                pySet(frame, idx, color_index)
            }
            idx = (idx + 1)
        }
    }
    return pyBytes(frame)
}

func run_06_julia_parameter_sweep() any {
    var width int = 320
    _ = width
    var height int = 240
    _ = height
    var frames_n int = 72
    _ = frames_n
    var max_iter int = 180
    _ = max_iter
    var out_path string = "sample/out/06_julia_parameter_sweep.gif"
    _ = out_path
    var start any = pyPerfCounter()
    _ = start
    var frames any = []any{}
    _ = frames
    var center_cr float64 = (-0.745)
    _ = center_cr
    var center_ci float64 = 0.186
    _ = center_ci
    var radius_cr float64 = 0.12
    _ = radius_cr
    var radius_ci float64 = 0.1
    _ = radius_ci
    var start_offset int = 20
    _ = start_offset
    var phase_offset int = 180
    _ = phase_offset
    __pytra_range_start_13 := pyToInt(0)
    __pytra_range_stop_14 := pyToInt(frames_n)
    __pytra_range_step_15 := pyToInt(1)
    if __pytra_range_step_15 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_16 := __pytra_range_start_13; (__pytra_range_step_15 > 0 && __pytra_i_16 < __pytra_range_stop_14) || (__pytra_range_step_15 < 0 && __pytra_i_16 > __pytra_range_stop_14); __pytra_i_16 += __pytra_range_step_15 {
        i = __pytra_i_16
        var t float64 = (float64(((i + start_offset) % frames_n)) / float64(frames_n))
        _ = t
        var angle any = pyMul(pyMul(2.0, pyMathPi()), t)
        _ = angle
        var cr float64 = (center_cr + (radius_cr * math.Cos(pyToFloat(angle))))
        _ = cr
        var ci float64 = (center_ci + (radius_ci * math.Sin(pyToFloat(angle))))
        _ = ci
        var phase int = ((phase_offset + (i * 5)) % 255)
        _ = phase
        frames = pyAppend(frames, render_frame(width, height, cr, ci, max_iter, phase))
    }
    pySaveGIF(out_path, width, height, frames, julia_palette(), 8, 0)
    var elapsed any = pySub(pyPerfCounter(), start)
    _ = elapsed
    pyPrint("output:", out_path)
    pyPrint("frames:", frames_n)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func main() {
    run_06_julia_parameter_sweep()
}
```
</details>

<details>
<summary>Javaへの変換例 : 06_julia_parameter_sweep.java</summary>

```java
// このファイルは自動生成です（Python -> Java native mode）。

// Java ネイティブ変換向け Python 互換ランタイム補助。

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

final class PyRuntime {
    private PyRuntime() {
    }

    static String pyToString(Object v) {
        if (v == null) {
            return "None";
        }
        if (v instanceof Boolean b) {
            return b ? "True" : "False";
        }
        if (v instanceof List<?> list) {
            StringJoiner sj = new StringJoiner(", ", "[", "]");
            for (Object it : list) {
                sj.add(pyToString(it));
            }
            return sj.toString();
        }
        if (v instanceof Map<?, ?> map) {
            StringJoiner sj = new StringJoiner(", ", "{", "}");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                sj.add(pyToString(e.getKey()) + ": " + pyToString(e.getValue()));
            }
            return sj.toString();
        }
        return String.valueOf(v);
    }

    static void pyPrint(Object... values) {
        StringJoiner sj = new StringJoiner(" ");
        for (Object value : values) {
            sj.add(pyToString(value));
        }
        System.out.println(sj);
    }

    static boolean pyBool(Object v) {
        if (v == null) {
            return false;
        }
        if (v instanceof Boolean b) {
            return b;
        }
        if (v instanceof Integer i) {
            return i != 0;
        }
        if (v instanceof Long i) {
            return i != 0L;
        }
        if (v instanceof Double d) {
            return d != 0.0;
        }
        if (v instanceof String s) {
            return !s.isEmpty();
        }
        if (v instanceof List<?> list) {
            return !list.isEmpty();
        }
        if (v instanceof Map<?, ?> map) {
            return !map.isEmpty();
        }
        return true;
    }

    static int pyLen(Object v) {
        if (v instanceof String s) {
            return s.length();
        }
        if (v instanceof List<?> list) {
            return list.size();
        }
        if (v instanceof byte[] bytes) {
            return bytes.length;
        }
        if (v instanceof Map<?, ?> map) {
            return map.size();
        }
        throw new RuntimeException("len() unsupported type");
    }

    static List<Object> pyRange(int start, int stop, int step) {
        if (step == 0) {
            throw new RuntimeException("range() step must not be zero");
        }
        List<Object> out = new ArrayList<>();
        if (step > 0) {
            for (int i = start; i < stop; i += step) {
                out.add(i);
            }
        } else {
            for (int i = start; i > stop; i += step) {
                out.add(i);
            }
        }
        return out;
    }

    static double pyToFloat(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return i;
        }
        if (v instanceof Double d) {
            return d;
        }
        if (v instanceof Boolean b) {
            return b ? 1.0 : 0.0;
        }
        throw new RuntimeException("cannot convert to float");
    }

    static int pyToInt(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return (int) i.longValue();
        }
        if (v instanceof Double d) {
            // Python の int() は小数部切り捨て（0方向）なので Java のキャストで合わせる。
            return (int) d.doubleValue();
        }
        if (v instanceof Boolean b) {
            return b ? 1 : 0;
        }
        throw new RuntimeException("cannot convert to int");
    }

    static long pyToLong(Object v) {
        if (v instanceof Integer i) {
            return i.longValue();
        }
        if (v instanceof Long i) {
            return i.longValue();
        }
        if (v instanceof Double d) {
            return (long) d.doubleValue();
        }
        if (v instanceof Boolean b) {
            return b ? 1L : 0L;
        }
        throw new RuntimeException("cannot convert to long");
    }

    static Object pyAdd(Object a, Object b) {
        if (a instanceof String || b instanceof String) {
            return pyToString(a) + pyToString(b);
        }
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) + pyToLong(b);
        }
        return pyToFloat(a) + pyToFloat(b);
    }

    static Object pySub(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) - pyToLong(b);
        }
        return pyToFloat(a) - pyToFloat(b);
    }

    static Object pyMul(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) * pyToLong(b);
        }
        return pyToFloat(a) * pyToFloat(b);
    }

    static Object pyDiv(Object a, Object b) {
        return pyToFloat(a) / pyToFloat(b);
    }

    static Object pyFloorDiv(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long q = ai / bi;
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                q -= 1;
            }
            return q;
        }
        return (int) Math.floor(pyToFloat(a) / pyToFloat(b));
    }

    static Object pyMod(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                r += bi;
            }
            return r;
        }
        throw new RuntimeException("mod unsupported type");
    }

    static Object pyMin(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("min() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) < pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) < pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) < pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object pyMax(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("max() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) > pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) > pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) > pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object pyLShift(Object a, Object b) {
        return pyToInt(a) << pyToInt(b);
    }

    static Object pyRShift(Object a, Object b) {
        return pyToInt(a) >> pyToInt(b);
    }

    static Object pyBitAnd(Object a, Object b) {
        return pyToInt(a) & pyToInt(b);
    }

    static Object pyBitOr(Object a, Object b) {
        return pyToInt(a) | pyToInt(b);
    }

    static Object pyBitXor(Object a, Object b) {
        return pyToInt(a) ^ pyToInt(b);
    }

    static Object pyNeg(Object a) {
        if (a instanceof Integer || a instanceof Long || a instanceof Boolean) {
            return -pyToLong(a);
        }
        return -pyToFloat(a);
    }

    static boolean pyEq(Object a, Object b) {
        return pyToString(a).equals(pyToString(b));
    }

    static boolean pyNe(Object a, Object b) {
        return !pyEq(a, b);
    }

    static boolean pyLt(Object a, Object b) {
        return pyToFloat(a) < pyToFloat(b);
    }

    static boolean pyLe(Object a, Object b) {
        return pyToFloat(a) <= pyToFloat(b);
    }

    static boolean pyGt(Object a, Object b) {
        return pyToFloat(a) > pyToFloat(b);
    }

    static boolean pyGe(Object a, Object b) {
        return pyToFloat(a) >= pyToFloat(b);
    }

    static boolean pyIn(Object item, Object container) {
        if (container instanceof String s) {
            return s.contains(pyToString(item));
        }
        if (container instanceof List<?> list) {
            for (Object v : list) {
                if (pyEq(v, item)) {
                    return true;
                }
            }
            return false;
        }
        if (container instanceof Map<?, ?> map) {
            return map.containsKey(item);
        }
        return false;
    }

    static List<Object> pyIter(Object value) {
        if (value instanceof List<?> list) {
            return new ArrayList<>((List<Object>) list);
        }
        if (value instanceof byte[] arr) {
            List<Object> out = new ArrayList<>();
            for (byte b : arr) {
                out.add((int) (b & 0xff));
            }
            return out;
        }
        if (value instanceof String s) {
            List<Object> out = new ArrayList<>();
            for (int i = 0; i < s.length(); i++) {
                out.add(String.valueOf(s.charAt(i)));
            }
            return out;
        }
        if (value instanceof Map<?, ?> map) {
            return new ArrayList<>(((Map<Object, Object>) map).keySet());
        }
        throw new RuntimeException("iter unsupported");
    }

    static Object pyTernary(boolean cond, Object a, Object b) {
        return cond ? a : b;
    }

    static Object pyListFromIter(Object value) {
        return pyIter(value);
    }

    static Object pySlice(Object value, Object start, Object end) {
        if (value instanceof String s) {
            int n = s.length();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return s.substring(st, ed);
        }
        if (value instanceof List<?> list) {
            int n = list.size();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return new ArrayList<>(list.subList(st, ed));
        }
        throw new RuntimeException("slice unsupported");
    }

    static Object pyGet(Object value, Object key) {
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            if (i < 0)
                i += list.size();
            return list.get(i);
        }
        if (value instanceof Map<?, ?> map) {
            return ((Map<Object, Object>) map).get(key);
        }
        if (value instanceof String s) {
            int i = pyToInt(key);
            if (i < 0)
                i += s.length();
            return String.valueOf(s.charAt(i));
        }
        throw new RuntimeException("subscript unsupported");
    }

    static void pySet(Object value, Object key, Object newValue) {
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            List<Object> l = (List<Object>) list;
            if (i < 0)
                i += l.size();
            l.set(i, newValue);
            return;
        }
        if (value instanceof Map<?, ?> map) {
            ((Map<Object, Object>) map).put(key, newValue);
            return;
        }
        throw new RuntimeException("setitem unsupported");
    }

    static Object pyPop(Object value, Object idx) {
        if (value instanceof List<?> list) {
            List<Object> l = (List<Object>) list;
            int i = (idx == null) ? (l.size() - 1) : pyToInt(idx);
            if (i < 0)
                i += l.size();
            Object out = l.get(i);
            l.remove(i);
            return out;
        }
        throw new RuntimeException("pop unsupported");
    }

    static Object pyOrd(Object v) {
        String s = pyToString(v);
        return (int) s.charAt(0);
    }

    static Object pyChr(Object v) {
        return Character.toString((char) pyToInt(v));
    }

    static Object pyBytearray(Object size) {
        int n = (size == null) ? 0 : pyToInt(size);
        List<Object> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            out.add(0);
        }
        return out;
    }

    static Object pyBytes(Object v) {
        return v;
    }

    static boolean pyIsDigit(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
        }
        return true;
    }

    static boolean pyIsAlpha(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) {
                return false;
            }
        }
        return true;
    }

    static List<Object> pyList(Object... items) {
        List<Object> out = new ArrayList<>();
        for (Object item : items) {
            out.add(item);
        }
        return out;
    }

    static Map<Object, Object> pyDict(Object... kv) {
        Map<Object, Object> out = new HashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            out.put(kv[i], kv[i + 1]);
        }
        return out;
    }

    // --- time/math ---

    static Object pyPerfCounter() {
        return System.nanoTime() / 1_000_000_000.0;
    }

    static Object pyMathSqrt(Object v) {
        return Math.sqrt(pyToFloat(v));
    }

    static Object pyMathSin(Object v) {
        return Math.sin(pyToFloat(v));
    }

    static Object pyMathCos(Object v) {
        return Math.cos(pyToFloat(v));
    }

    static Object pyMathExp(Object v) {
        return Math.exp(pyToFloat(v));
    }

    static Object pyMathFloor(Object v) {
        return Math.floor(pyToFloat(v));
    }

    static Object pyMathPi() {
        return Math.PI;
    }

    // --- png/gif ---

    static byte[] pyToBytes(Object v) {
        if (v instanceof byte[] b) {
            return b;
        }
        if (v instanceof List<?> list) {
            byte[] out = new byte[list.size()];
            for (int i = 0; i < list.size(); i++) {
                out[i] = (byte) pyToInt(list.get(i));
            }
            return out;
        }
        if (v instanceof String s) {
            return s.getBytes(StandardCharsets.UTF_8);
        }
        throw new RuntimeException("cannot convert to bytes");
    }

    static byte[] pyChunk(String chunkType, byte[] data) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            int n = data.length;
            out.write((n >>> 24) & 0xff);
            out.write((n >>> 16) & 0xff);
            out.write((n >>> 8) & 0xff);
            out.write(n & 0xff);
            byte[] typeBytes = chunkType.getBytes(StandardCharsets.US_ASCII);
            out.write(typeBytes);
            out.write(data);
            CRC32 crc = new CRC32();
            crc.update(typeBytes);
            crc.update(data);
            long c = crc.getValue();
            out.write((int) ((c >>> 24) & 0xff));
            out.write((int) ((c >>> 16) & 0xff));
            out.write((int) ((c >>> 8) & 0xff));
            out.write((int) (c & 0xff));
            return out.toByteArray();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static void pyWriteRGBPNG(Object path, Object width, Object height, Object pixels) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        byte[] raw = pyToBytes(pixels);
        int expected = w * h * 3;
        if (raw.length != expected) {
            throw new RuntimeException("pixels length mismatch");
        }

        byte[] scan = new byte[h * (1 + w * 3)];
        int rowBytes = w * 3;
        int pos = 0;
        for (int y = 0; y < h; y++) {
            scan[pos++] = 0;
            int start = y * rowBytes;
            System.arraycopy(raw, start, scan, pos, rowBytes);
            pos += rowBytes;
        }

        Deflater deflater = new Deflater(6);
        deflater.setInput(scan);
        deflater.finish();
        byte[] buf = new byte[8192];
        ByteArrayOutputStream zOut = new ByteArrayOutputStream();
        while (!deflater.finished()) {
            int n = deflater.deflate(buf);
            zOut.write(buf, 0, n);
        }
        byte[] idat = zOut.toByteArray();

        byte[] ihdr = new byte[] {
                (byte) (w >>> 24), (byte) (w >>> 16), (byte) (w >>> 8), (byte) w,
                (byte) (h >>> 24), (byte) (h >>> 16), (byte) (h >>> 8), (byte) h,
                8, 2, 0, 0, 0
        };

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            fos.write(new byte[] { (byte) 0x89, 'P', 'N', 'G', '
', '
', 0x1a, '
' });
            fos.write(pyChunk("IHDR", ihdr));
            fos.write(pyChunk("IDAT", idat));
            fos.write(pyChunk("IEND", new byte[0]));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static byte[] pyLzwEncode(byte[] data, int minCodeSize) {
        if (data.length == 0) {
            return new byte[0];
        }
        int clearCode = 1 << minCodeSize;
        int endCode = clearCode + 1;
        int codeSize = minCodeSize + 1;

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        int bitBuffer = 0;
        int bitCount = 0;
        int[] codes = new int[data.length * 2 + 2];
        int k = 0;
        codes[k++] = clearCode;
        for (byte b : data) {
            codes[k++] = b & 0xff;
            codes[k++] = clearCode;
        }
        codes[k++] = endCode;
        for (int i = 0; i < k; i++) {
            int code = codes[i];
            bitBuffer |= (code << bitCount);
            bitCount += codeSize;
            while (bitCount >= 8) {
                out.write(bitBuffer & 0xff);
                bitBuffer >>>= 8;
                bitCount -= 8;
            }
        }
        if (bitCount > 0) {
            out.write(bitBuffer & 0xff);
        }
        return out.toByteArray();
    }

    static Object pyGrayscalePalette() {
        byte[] p = new byte[256 * 3];
        for (int i = 0; i < 256; i++) {
            p[i * 3] = (byte) i;
            p[i * 3 + 1] = (byte) i;
            p[i * 3 + 2] = (byte) i;
        }
        return p;
    }

    static void pySaveGif(Object path, Object width, Object height, Object frames, Object palette, Object delayCs, Object loop) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        int frameBytes = w * h;
        byte[] pal = pyToBytes(palette);
        if (pal.length != 256 * 3) {
            throw new RuntimeException("palette must be 256*3 bytes");
        }
        int dcs = pyToInt(delayCs);
        int lp = pyToInt(loop);

        List<Object> frs = pyIter(frames);

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write("GIF89a".getBytes(StandardCharsets.US_ASCII));
            out.write(w & 0xff);
            out.write((w >>> 8) & 0xff);
            out.write(h & 0xff);
            out.write((h >>> 8) & 0xff);
            out.write(0xF7);
            out.write(0);
            out.write(0);
            out.write(pal);
            out.write(new byte[] { 0x21, (byte) 0xFF, 0x0B });
            out.write("NETSCAPE2.0".getBytes(StandardCharsets.US_ASCII));
            out.write(new byte[] { 0x03, 0x01, (byte) (lp & 0xff), (byte) ((lp >>> 8) & 0xff), 0x00 });

            for (Object frAny : frs) {
                byte[] fr = pyToBytes(frAny);
                if (fr.length != frameBytes) {
                    throw new RuntimeException("frame size mismatch");
                }
                out.write(new byte[] { 0x21, (byte) 0xF9, 0x04, 0x00, (byte) (dcs & 0xff), (byte) ((dcs >>> 8) & 0xff), 0x00, 0x00 });
                out.write(0x2C);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(w & 0xff);
                out.write((w >>> 8) & 0xff);
                out.write(h & 0xff);
                out.write((h >>> 8) & 0xff);
                out.write(0x00);
                out.write(0x08);
                byte[] compressed = pyLzwEncode(fr, 8);
                int pos = 0;
                while (pos < compressed.length) {
                    int len = Math.min(255, compressed.length - pos);
                    out.write(len);
                    out.write(compressed, pos, len);
                    pos += len;
                }
                out.write(0x00);
            }
            out.write(0x3B);
            fos.write(out.toByteArray());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}

class pytra_06_julia_parameter_sweep {
    static Object julia_palette() {
        Object palette = PyRuntime.pyBytearray(PyRuntime.pyMul(256, 3));
        PyRuntime.pySet(palette, 0, 0);
        PyRuntime.pySet(palette, 1, 0);
        PyRuntime.pySet(palette, 2, 0);
        int __pytra_range_start_1 = PyRuntime.pyToInt(1);
        int __pytra_range_stop_2 = PyRuntime.pyToInt(256);
        int __pytra_range_step_3 = PyRuntime.pyToInt(1);
        if (__pytra_range_step_3 == 0) { throw new RuntimeException("range() step must not be zero"); }
        Object i = null;
        for (int __pytra_i_4 = __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3) {
            i = __pytra_i_4;
            Object t = PyRuntime.pyDiv(PyRuntime.pySub(i, 1), 254.0);
            Object r = PyRuntime.pyToInt(PyRuntime.pyMul(255.0, PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(9.0, PyRuntime.pySub(1.0, t)), t), t), t)));
            Object g = PyRuntime.pyToInt(PyRuntime.pyMul(255.0, PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(15.0, PyRuntime.pySub(1.0, t)), PyRuntime.pySub(1.0, t)), t), t)));
            Object b = PyRuntime.pyToInt(PyRuntime.pyMul(255.0, PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(8.5, PyRuntime.pySub(1.0, t)), PyRuntime.pySub(1.0, t)), PyRuntime.pySub(1.0, t)), t)));
            PyRuntime.pySet(palette, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 0), r);
            PyRuntime.pySet(palette, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 1), g);
            PyRuntime.pySet(palette, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 2), b);
        }
        return PyRuntime.pyBytes(palette);
    }
    static Object render_frame(Object width, Object height, Object cr, Object ci, Object max_iter, Object phase) {
        Object frame = PyRuntime.pyBytearray(PyRuntime.pyMul(width, height));
        Object idx = 0;
        int __pytra_range_start_5 = PyRuntime.pyToInt(0);
        int __pytra_range_stop_6 = PyRuntime.pyToInt(height);
        int __pytra_range_step_7 = PyRuntime.pyToInt(1);
        if (__pytra_range_step_7 == 0) { throw new RuntimeException("range() step must not be zero"); }
        Object y = null;
        for (int __pytra_i_8 = __pytra_range_start_5; (__pytra_range_step_7 > 0 && __pytra_i_8 < __pytra_range_stop_6) || (__pytra_range_step_7 < 0 && __pytra_i_8 > __pytra_range_stop_6); __pytra_i_8 += __pytra_range_step_7) {
            y = __pytra_i_8;
            Object zy0 = PyRuntime.pyAdd(PyRuntime.pyNeg(1.2), PyRuntime.pyMul(2.4, PyRuntime.pyDiv(y, PyRuntime.pySub(height, 1))));
            int __pytra_range_start_9 = PyRuntime.pyToInt(0);
            int __pytra_range_stop_10 = PyRuntime.pyToInt(width);
            int __pytra_range_step_11 = PyRuntime.pyToInt(1);
            if (__pytra_range_step_11 == 0) { throw new RuntimeException("range() step must not be zero"); }
            Object x = null;
            for (int __pytra_i_12 = __pytra_range_start_9; (__pytra_range_step_11 > 0 && __pytra_i_12 < __pytra_range_stop_10) || (__pytra_range_step_11 < 0 && __pytra_i_12 > __pytra_range_stop_10); __pytra_i_12 += __pytra_range_step_11) {
                x = __pytra_i_12;
                Object zx = PyRuntime.pyAdd(PyRuntime.pyNeg(1.8), PyRuntime.pyMul(3.6, PyRuntime.pyDiv(x, PyRuntime.pySub(width, 1))));
                Object zy = zy0;
                Object i = 0;
                while (PyRuntime.pyBool(PyRuntime.pyLt(i, max_iter))) {
                    Object zx2 = PyRuntime.pyMul(zx, zx);
                    Object zy2 = PyRuntime.pyMul(zy, zy);
                    if (PyRuntime.pyBool(PyRuntime.pyGt(PyRuntime.pyAdd(zx2, zy2), 4.0))) {
                        break;
                    }
                    zy = PyRuntime.pyAdd(PyRuntime.pyMul(PyRuntime.pyMul(2.0, zx), zy), ci);
                    zx = PyRuntime.pyAdd(PyRuntime.pySub(zx2, zy2), cr);
                    i = PyRuntime.pyAdd(i, 1);
                }
                if (PyRuntime.pyBool(PyRuntime.pyGe(i, max_iter))) {
                    PyRuntime.pySet(frame, idx, 0);
                } else {
                    Object color_index = PyRuntime.pyAdd(1, PyRuntime.pyMod(PyRuntime.pyAdd(PyRuntime.pyFloorDiv(PyRuntime.pyMul(i, 224), max_iter), phase), 255));
                    PyRuntime.pySet(frame, idx, color_index);
                }
                idx = PyRuntime.pyAdd(idx, 1);
            }
        }
        return PyRuntime.pyBytes(frame);
    }
    static Object run_06_julia_parameter_sweep() {
        Object width = 320;
        Object height = 240;
        Object frames_n = 72;
        Object max_iter = 180;
        Object out_path = "sample/out/06_julia_parameter_sweep.gif";
        Object start = PyRuntime.pyPerfCounter();
        Object frames = PyRuntime.pyList();
        Object center_cr = PyRuntime.pyNeg(0.745);
        Object center_ci = 0.186;
        Object radius_cr = 0.12;
        Object radius_ci = 0.1;
        Object start_offset = 20;
        Object phase_offset = 180;
        int __pytra_range_start_13 = PyRuntime.pyToInt(0);
        int __pytra_range_stop_14 = PyRuntime.pyToInt(frames_n);
        int __pytra_range_step_15 = PyRuntime.pyToInt(1);
        if (__pytra_range_step_15 == 0) { throw new RuntimeException("range() step must not be zero"); }
        Object i = null;
        for (int __pytra_i_16 = __pytra_range_start_13; (__pytra_range_step_15 > 0 && __pytra_i_16 < __pytra_range_stop_14) || (__pytra_range_step_15 < 0 && __pytra_i_16 > __pytra_range_stop_14); __pytra_i_16 += __pytra_range_step_15) {
            i = __pytra_i_16;
            Object t = PyRuntime.pyDiv(PyRuntime.pyMod(PyRuntime.pyAdd(i, start_offset), frames_n), frames_n);
            Object angle = PyRuntime.pyMul(PyRuntime.pyMul(2.0, PyRuntime.pyMathPi()), t);
            Object cr = PyRuntime.pyAdd(center_cr, PyRuntime.pyMul(radius_cr, PyRuntime.pyMathCos(angle)));
            Object ci = PyRuntime.pyAdd(center_ci, PyRuntime.pyMul(radius_ci, PyRuntime.pyMathSin(angle)));
            Object phase = PyRuntime.pyMod(PyRuntime.pyAdd(phase_offset, PyRuntime.pyMul(i, 5)), 255);
            ((java.util.List<Object>)frames).add(render_frame(width, height, cr, ci, max_iter, phase));
        }
        PyRuntime.pySaveGif(out_path, width, height, frames, julia_palette(), 8, 0);
        Object elapsed = PyRuntime.pySub(PyRuntime.pyPerfCounter(), start);
        PyRuntime.pyPrint("output:", out_path);
        PyRuntime.pyPrint("frames:", frames_n);
        PyRuntime.pyPrint("elapsed_sec:", elapsed);
        return null;
    }

    public static void main(String[] args) {
        run_06_julia_parameter_sweep();
    }
}
```
</details>

<details>
<summary>Swiftへの変換例 : 06_julia_parameter_sweep.swift</summary>

```swift
// このファイルは自動生成です（Python -> Swift node-backed mode）。

// Swift 実行向け Node.js ランタイム補助。

import Foundation

/// Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
/// - Parameters:
///   - sourceBase64: JavaScript ソースコードの Base64 文字列。
///   - args: JavaScript 側へ渡す引数配列。
/// - Returns:
///   node プロセスの終了コード。失敗時は 1 を返す。
func pytraRunEmbeddedNode(_ sourceBase64: String, _ args: [String]) -> Int32 {
    guard let sourceData = Data(base64Encoded: sourceBase64) else {
        fputs("error: failed to decode embedded JavaScript source
", stderr)
        return 1
    }

    let tmpDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
    let fileName = "pytra_embedded_\(UUID().uuidString).js"
    let scriptURL = tmpDir.appendingPathComponent(fileName)

    do {
        try sourceData.write(to: scriptURL)
    } catch {
        fputs("error: failed to write temporary JavaScript file: \(error)
", stderr)
        return 1
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    process.arguments = ["node", scriptURL.path] + args
    process.environment = ProcessInfo.processInfo.environment
    process.standardInput = FileHandle.standardInput
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError

    do {
        try process.run()
        process.waitUntilExit()
    } catch {
        fputs("error: failed to launch node: \(error)
", stderr)
        try? FileManager.default.removeItem(at: scriptURL)
        return 1
    }

    try? FileManager.default.removeItem(at: scriptURL)
    return process.terminationStatus
}

// 埋め込み JavaScript ソース（Base64）。
let pytraEmbeddedJsBase64 = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24ganVsaWFfcGFsZXR0ZSgpIHsKICAgIGxldCBwYWxldHRlID0gcHlCeXRlYXJyYXkoKCgyNTYpICogKDMpKSk7CiAgICBwYWxldHRlWzBdID0gMDsKICAgIHBhbGV0dGVbMV0gPSAwOwogICAgcGFsZXR0ZVsyXSA9IDA7CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMTsgX19weXRyYV9pXzEgPCAyNTY7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHQgPSAoKCgoaSkgLSAoMSkpKSAvICgyNTQuMCkpOwogICAgICAgIGxldCByID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAoKCgoKCgoKCg5LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGcgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDE1LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGIgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDguNSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICgoKDEuMCkgLSAodCkpKSkpICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSkpKTsKICAgICAgICBwYWxldHRlWygoKChpKSAqICgzKSkpICsgKDApKV0gPSByOwogICAgICAgIHBhbGV0dGVbKCgoKGkpICogKDMpKSkgKyAoMSkpXSA9IGc7CiAgICAgICAgcGFsZXR0ZVsoKCgoaSkgKiAoMykpKSArICgyKSldID0gYjsKICAgIH0KICAgIHJldHVybiBweUJ5dGVzKHBhbGV0dGUpOwp9CmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjciwgY2ksIG1heF9pdGVyLCBwaGFzZSkgewogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGlkeCA9IDA7CiAgICBsZXQgeTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8yID0gMDsgX19weXRyYV9pXzIgPCBoZWlnaHQ7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICB5ID0gX19weXRyYV9pXzI7CiAgICAgICAgbGV0IHp5MCA9ICgoKC0oMS4yKSkpICsgKCgoMi40KSAqICgoKHkpIC8gKCgoaGVpZ2h0KSAtICgxKSkpKSkpKSk7CiAgICAgICAgbGV0IHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzMgPSAwOyBfX3B5dHJhX2lfMyA8IHdpZHRoOyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgbGV0IHp4ID0gKCgoLSgxLjgpKSkgKyAoKCgzLjYpICogKCgoeCkgLyAoKCh3aWR0aCkgLSAoMSkpKSkpKSkpOwogICAgICAgICAgICBsZXQgenkgPSB6eTA7CiAgICAgICAgICAgIGxldCBpID0gMDsKICAgICAgICAgICAgd2hpbGUgKHB5Qm9vbCgoKGkpIDwgKG1heF9pdGVyKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgengyID0gKCh6eCkgKiAoengpKTsKICAgICAgICAgICAgICAgIGxldCB6eTIgPSAoKHp5KSAqICh6eSkpOwogICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKCgoengyKSArICh6eTIpKSkgPiAoNC4wKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICB6eSA9ICgoKCgoKDIuMCkgKiAoengpKSkgKiAoenkpKSkgKyAoY2kpKTsKICAgICAgICAgICAgICAgIHp4ID0gKCgoKHp4MikgLSAoenkyKSkpICsgKGNyKSk7CiAgICAgICAgICAgICAgICBpID0gaSArIDE7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGkpID49IChtYXhfaXRlcikpKSkgewogICAgICAgICAgICAgICAgZnJhbWVbaWR4XSA9IDA7CiAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICBsZXQgY29sb3JfaW5kZXggPSAoKDEpICsgKHB5TW9kKCgocHlGbG9vckRpdigoKGkpICogKDIyNCkpLCBtYXhfaXRlcikpICsgKHBoYXNlKSksIDI1NSkpKTsKICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSBjb2xvcl9pbmRleDsKICAgICAgICAgICAgfQogICAgICAgICAgICBpZHggPSBpZHggKyAxOwogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwKCkgewogICAgbGV0IHdpZHRoID0gMzIwOwogICAgbGV0IGhlaWdodCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDcyOwogICAgbGV0IG1heF9pdGVyID0gMTgwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBjZW50ZXJfY3IgPSAoLSgwLjc0NSkpOwogICAgbGV0IGNlbnRlcl9jaSA9IDAuMTg2OwogICAgbGV0IHJhZGl1c19jciA9IDAuMTI7CiAgICBsZXQgcmFkaXVzX2NpID0gMC4xOwogICAgbGV0IHN0YXJ0X29mZnNldCA9IDIwOwogICAgbGV0IHBoYXNlX29mZnNldCA9IDE4MDsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzQgPSAwOyBfX3B5dHJhX2lfNCA8IGZyYW1lc19uOyBfX3B5dHJhX2lfNCArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV80OwogICAgICAgIGxldCB0ID0gKChweU1vZCgoKGkpICsgKHN0YXJ0X29mZnNldCkpLCBmcmFtZXNfbikpIC8gKGZyYW1lc19uKSk7CiAgICAgICAgbGV0IGFuZ2xlID0gKCgoKDIuMCkgKiAobWF0aC5waSkpKSAqICh0KSk7CiAgICAgICAgbGV0IGNyID0gKChjZW50ZXJfY3IpICsgKCgocmFkaXVzX2NyKSAqIChtYXRoLmNvcyhhbmdsZSkpKSkpOwogICAgICAgIGxldCBjaSA9ICgoY2VudGVyX2NpKSArICgoKHJhZGl1c19jaSkgKiAobWF0aC5zaW4oYW5nbGUpKSkpKTsKICAgICAgICBsZXQgcGhhc2UgPSBweU1vZCgoKHBoYXNlX29mZnNldCkgKyAoKChpKSAqICg1KSkpKSwgMjU1KTsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY3IsIGNpLCBtYXhfaXRlciwgcGhhc2UpKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBmcmFtZXMsIGp1bGlhX3BhbGV0dGUoKSwgOCwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIGZyYW1lc19uKTsKICAgIHB5UHJpbnQoJ2VsYXBzZWRfc2VjOicsIGVsYXBzZWQpOwp9CnJ1bl8wNl9qdWxpYV9wYXJhbWV0ZXJfc3dlZXAoKTsK"
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)
Foundation.exit(pytraCode)
```
</details>

<details>
<summary>Kotlinへの変換例 : 06_julia_parameter_sweep.kt</summary>

```kotlin
// このファイルは自動生成です（Python -> Kotlin node-backed mode）。

// Kotlin 実行向け Node.js ランタイム補助。

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import java.util.UUID

/**
 * Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
 */
object PyRuntime {
    /**
     * @param sourceBase64 JavaScript ソースコードの Base64 文字列。
     * @param args JavaScript 側へ渡す引数配列。
     * @return node プロセスの終了コード。失敗時は 1 を返す。
     */
    @JvmStatic
    fun runEmbeddedNode(sourceBase64: String, args: Array<String>): Int {
        val sourceBytes: ByteArray = try {
            Base64.getDecoder().decode(sourceBase64)
        } catch (ex: IllegalArgumentException) {
            System.err.println("error: failed to decode embedded JavaScript source")
            return 1
        }

        val tempFile: Path = try {
            val name = "pytra_embedded_${UUID.randomUUID()}.js"
            val p = File(System.getProperty("java.io.tmpdir"), name).toPath()
            Files.write(p, sourceBytes)
            p
        } catch (ex: Exception) {
            System.err.println("error: failed to write temporary JavaScript file: ${ex.message}")
            return 1
        }

        val command = mutableListOf("node", tempFile.toString())
        command.addAll(args)
        val process: Process = try {
            ProcessBuilder(command)
                .inheritIO()
                .start()
        } catch (ex: Exception) {
            System.err.println("error: failed to launch node: ${ex.message}")
            try {
                Files.deleteIfExists(tempFile)
            } catch (_: Exception) {
            }
            return 1
        }

        val code = process.waitFor()
        try {
            Files.deleteIfExists(tempFile)
        } catch (_: Exception) {
        }
        return code
    }
}

class pytra_06_julia_parameter_sweep {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24ganVsaWFfcGFsZXR0ZSgpIHsKICAgIGxldCBwYWxldHRlID0gcHlCeXRlYXJyYXkoKCgyNTYpICogKDMpKSk7CiAgICBwYWxldHRlWzBdID0gMDsKICAgIHBhbGV0dGVbMV0gPSAwOwogICAgcGFsZXR0ZVsyXSA9IDA7CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMTsgX19weXRyYV9pXzEgPCAyNTY7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHQgPSAoKCgoaSkgLSAoMSkpKSAvICgyNTQuMCkpOwogICAgICAgIGxldCByID0gTWF0aC50cnVuYyhOdW1iZXIoKCgyNTUuMCkgKiAoKCgoKCgoKCg5LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGcgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDE1LjApICogKCgoMS4wKSAtICh0KSkpKSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICh0KSkpICogKHQpKSkpKSk7CiAgICAgICAgbGV0IGIgPSBNYXRoLnRydW5jKE51bWJlcigoKDI1NS4wKSAqICgoKCgoKCgoKDguNSkgKiAoKCgxLjApIC0gKHQpKSkpKSAqICgoKDEuMCkgLSAodCkpKSkpICogKCgoMS4wKSAtICh0KSkpKSkgKiAodCkpKSkpKTsKICAgICAgICBwYWxldHRlWygoKChpKSAqICgzKSkpICsgKDApKV0gPSByOwogICAgICAgIHBhbGV0dGVbKCgoKGkpICogKDMpKSkgKyAoMSkpXSA9IGc7CiAgICAgICAgcGFsZXR0ZVsoKCgoaSkgKiAoMykpKSArICgyKSldID0gYjsKICAgIH0KICAgIHJldHVybiBweUJ5dGVzKHBhbGV0dGUpOwp9CmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBjciwgY2ksIG1heF9pdGVyLCBwaGFzZSkgewogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGlkeCA9IDA7CiAgICBsZXQgeTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8yID0gMDsgX19weXRyYV9pXzIgPCBoZWlnaHQ7IF9fcHl0cmFfaV8yICs9IDEpIHsKICAgICAgICB5ID0gX19weXRyYV9pXzI7CiAgICAgICAgbGV0IHp5MCA9ICgoKC0oMS4yKSkpICsgKCgoMi40KSAqICgoKHkpIC8gKCgoaGVpZ2h0KSAtICgxKSkpKSkpKSk7CiAgICAgICAgbGV0IHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzMgPSAwOyBfX3B5dHJhX2lfMyA8IHdpZHRoOyBfX3B5dHJhX2lfMyArPSAxKSB7CiAgICAgICAgICAgIHggPSBfX3B5dHJhX2lfMzsKICAgICAgICAgICAgbGV0IHp4ID0gKCgoLSgxLjgpKSkgKyAoKCgzLjYpICogKCgoeCkgLyAoKCh3aWR0aCkgLSAoMSkpKSkpKSkpOwogICAgICAgICAgICBsZXQgenkgPSB6eTA7CiAgICAgICAgICAgIGxldCBpID0gMDsKICAgICAgICAgICAgd2hpbGUgKHB5Qm9vbCgoKGkpIDwgKG1heF9pdGVyKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgengyID0gKCh6eCkgKiAoengpKTsKICAgICAgICAgICAgICAgIGxldCB6eTIgPSAoKHp5KSAqICh6eSkpOwogICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKCgoengyKSArICh6eTIpKSkgPiAoNC4wKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYnJlYWs7CiAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICB6eSA9ICgoKCgoKDIuMCkgKiAoengpKSkgKiAoenkpKSkgKyAoY2kpKTsKICAgICAgICAgICAgICAgIHp4ID0gKCgoKHp4MikgLSAoenkyKSkpICsgKGNyKSk7CiAgICAgICAgICAgICAgICBpID0gaSArIDE7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGkpID49IChtYXhfaXRlcikpKSkgewogICAgICAgICAgICAgICAgZnJhbWVbaWR4XSA9IDA7CiAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICBsZXQgY29sb3JfaW5kZXggPSAoKDEpICsgKHB5TW9kKCgocHlGbG9vckRpdigoKGkpICogKDIyNCkpLCBtYXhfaXRlcikpICsgKHBoYXNlKSksIDI1NSkpKTsKICAgICAgICAgICAgICAgIGZyYW1lW2lkeF0gPSBjb2xvcl9pbmRleDsKICAgICAgICAgICAgfQogICAgICAgICAgICBpZHggPSBpZHggKyAxOwogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwKCkgewogICAgbGV0IHdpZHRoID0gMzIwOwogICAgbGV0IGhlaWdodCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDcyOwogICAgbGV0IG1heF9pdGVyID0gMTgwOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMDZfanVsaWFfcGFyYW1ldGVyX3N3ZWVwLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBjZW50ZXJfY3IgPSAoLSgwLjc0NSkpOwogICAgbGV0IGNlbnRlcl9jaSA9IDAuMTg2OwogICAgbGV0IHJhZGl1c19jciA9IDAuMTI7CiAgICBsZXQgcmFkaXVzX2NpID0gMC4xOwogICAgbGV0IHN0YXJ0X29mZnNldCA9IDIwOwogICAgbGV0IHBoYXNlX29mZnNldCA9IDE4MDsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzQgPSAwOyBfX3B5dHJhX2lfNCA8IGZyYW1lc19uOyBfX3B5dHJhX2lfNCArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV80OwogICAgICAgIGxldCB0ID0gKChweU1vZCgoKGkpICsgKHN0YXJ0X29mZnNldCkpLCBmcmFtZXNfbikpIC8gKGZyYW1lc19uKSk7CiAgICAgICAgbGV0IGFuZ2xlID0gKCgoKDIuMCkgKiAobWF0aC5waSkpKSAqICh0KSk7CiAgICAgICAgbGV0IGNyID0gKChjZW50ZXJfY3IpICsgKCgocmFkaXVzX2NyKSAqIChtYXRoLmNvcyhhbmdsZSkpKSkpOwogICAgICAgIGxldCBjaSA9ICgoY2VudGVyX2NpKSArICgoKHJhZGl1c19jaSkgKiAobWF0aC5zaW4oYW5nbGUpKSkpKTsKICAgICAgICBsZXQgcGhhc2UgPSBweU1vZCgoKHBoYXNlX29mZnNldCkgKyAoKChpKSAqICg1KSkpKSwgMjU1KTsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgY3IsIGNpLCBtYXhfaXRlciwgcGhhc2UpKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBmcmFtZXMsIGp1bGlhX3BhbGV0dGUoKSwgOCwgMCk7CiAgICBsZXQgZWxhcHNlZCA9ICgocGVyZl9jb3VudGVyKCkpIC0gKHN0YXJ0KSk7CiAgICBweVByaW50KCdvdXRwdXQ6Jywgb3V0X3BhdGgpOwogICAgcHlQcmludCgnZnJhbWVzOicsIGZyYW1lc19uKTsKICAgIHB5UHJpbnQoJ2VsYXBzZWRfc2VjOicsIGVsYXBzZWQpOwp9CnJ1bl8wNl9qdWxpYV9wYXJhbWV0ZXJfc3dlZXAoKTsK"

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
```
</details>

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

from py_module.gif_helper import save_gif


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
<summary>変換後コード（C++ | Rust | C# | JavaScript | TypeScript | Go | Java | Swift | Kotlin）: 16_glass_sculpture_chaos</summary>

<details>
<summary>C++への変換例 : 16_glass_sculpture_chaos.cpp</summary>

```cpp
#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

double clamp01(double v)
{
    if ((v < 0.0))
    {
        return 0.0;
    }
    if ((v > 1.0))
    {
        return 1.0;
    }
    return v;
}

double dot(double ax, double ay, double az, double bx, double by, double bz)
{
    return (((ax * bx) + (ay * by)) + (az * bz));
}

double length(double x, double y, double z)
{
    return pycs::cpp_module::math::sqrt((((x * x) + (y * y)) + (z * z)));
}

tuple<double, double, double> normalize(double x, double y, double z)
{
    auto l = length(x, y, z);
    if ((l < 1e-09))
    {
        return std::make_tuple(0.0, 0.0, 0.0);
    }
    return std::make_tuple(py_div(x, l), py_div(y, l), py_div(z, l));
}

tuple<double, double, double> reflect(double ix, double iy, double iz, double nx, double ny, double nz)
{
    double d = (dot(ix, iy, iz, nx, ny, nz) * 2.0);
    return std::make_tuple((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)));
}

tuple<double, double, double> refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
{
    auto cosi = (-dot(ix, iy, iz, nx, ny, nz));
    auto sint2 = ((eta * eta) * (1.0 - (cosi * cosi)));
    if ((sint2 > 1.0))
    {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    auto cost = pycs::cpp_module::math::sqrt((1.0 - sint2));
    auto k = ((eta * cosi) - cost);
    return std::make_tuple(((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)));
}

double schlick(double cos_theta, double f0)
{
    double m = (1.0 - cos_theta);
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)));
}

tuple<double, double, double> sky_color(double dx, double dy, double dz, double tphase)
{
    double t = (0.5 * (dy + 1.0));
    double r = (0.06 + (0.2 * t));
    double g = (0.1 + (0.25 * t));
    double b = (0.16 + (0.45 * t));
    double band = (0.5 + (0.5 * pycs::cpp_module::math::sin((((8.0 * dx) + (6.0 * dz)) + tphase))));
    r = (r + (0.08 * band));
    g = (g + (0.05 * band));
    b = (b + (0.12 * band));
    return std::make_tuple(clamp01(r), clamp01(g), clamp01(b));
}

double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
{
    auto lx = (ox - cx);
    auto ly = (oy - cy);
    auto lz = (oz - cz);
    auto b = (((lx * dx) + (ly * dy)) + (lz * dz));
    auto c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius));
    auto h = ((b * b) - c);
    if ((h < 0.0))
    {
        return (-1.0);
    }
    auto s = pycs::cpp_module::math::sqrt(h);
    auto t0 = ((-b) - s);
    if ((t0 > 0.0001))
    {
        return t0;
    }
    auto t1 = ((-b) + s);
    if ((t1 > 0.0001))
    {
        return t1;
    }
    return (-1.0);
}

vector<uint8_t> palette_332()
{
    vector<uint8_t> p = py_bytearray((256 * 3));
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        long long r = ((i >> 5) & 7);
        long long g = ((i >> 2) & 7);
        long long b = (i & 3);
        p[((i * 3) + 0)] = static_cast<long long>(py_div((255 * r), 7));
        p[((i * 3) + 1)] = static_cast<long long>(py_div((255 * g), 7));
        p[((i * 3) + 2)] = static_cast<long long>(py_div((255 * b), 3));
    }
    return py_bytes(p);
}

long long quantize_332(double r, double g, double b)
{
    long long rr = static_cast<long long>((clamp01(r) * 255.0));
    long long gg = static_cast<long long>((clamp01(g) * 255.0));
    long long bb = static_cast<long long>((clamp01(b) * 255.0));
    return ((((rr >> 5) << 5) + ((gg >> 5) << 2)) + (bb >> 6));
}

vector<uint8_t> render_frame(long long width, long long height, long long frame_id, long long frames_n)
{
    double t = py_div(frame_id, frames_n);
    double tphase = ((2.0 * pycs::cpp_module::math::pi) * t);
    double cam_r = 3.0;
    auto cam_x = (cam_r * pycs::cpp_module::math::cos((tphase * 0.9)));
    double cam_y = (1.1 + (0.25 * pycs::cpp_module::math::sin((tphase * 0.6))));
    auto cam_z = (cam_r * pycs::cpp_module::math::sin((tphase * 0.9)));
    double look_x = 0.0;
    double look_y = 0.35;
    double look_z = 0.0;
    auto __pytra_tuple_4 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z));
    auto fwd_x = std::get<0>(__pytra_tuple_4);
    auto fwd_y = std::get<1>(__pytra_tuple_4);
    auto fwd_z = std::get<2>(__pytra_tuple_4);
    auto __pytra_tuple_5 = normalize(fwd_z, 0.0, (-fwd_x));
    auto right_x = std::get<0>(__pytra_tuple_5);
    auto right_y = std::get<1>(__pytra_tuple_5);
    auto right_z = std::get<2>(__pytra_tuple_5);
    auto __pytra_tuple_6 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)));
    auto up_x = std::get<0>(__pytra_tuple_6);
    auto up_y = std::get<1>(__pytra_tuple_6);
    auto up_z = std::get<2>(__pytra_tuple_6);
    double s0x = (0.9 * pycs::cpp_module::math::cos((1.3 * tphase)));
    double s0y = (0.15 + (0.35 * pycs::cpp_module::math::sin((1.7 * tphase))));
    double s0z = (0.9 * pycs::cpp_module::math::sin((1.3 * tphase)));
    double s1x = (1.2 * pycs::cpp_module::math::cos(((1.3 * tphase) + 2.094)));
    double s1y = (0.1 + (0.4 * pycs::cpp_module::math::sin(((1.1 * tphase) + 0.8))));
    double s1z = (1.2 * pycs::cpp_module::math::sin(((1.3 * tphase) + 2.094)));
    double s2x = (1.0 * pycs::cpp_module::math::cos(((1.3 * tphase) + 4.188)));
    double s2y = (0.2 + (0.3 * pycs::cpp_module::math::sin(((1.5 * tphase) + 1.9))));
    double s2z = (1.0 * pycs::cpp_module::math::sin(((1.3 * tphase) + 4.188)));
    double lr = 0.35;
    double lx = (2.4 * pycs::cpp_module::math::cos((tphase * 1.8)));
    double ly = (1.8 + (0.8 * pycs::cpp_module::math::sin((tphase * 1.2))));
    double lz = (2.4 * pycs::cpp_module::math::sin((tphase * 1.8)));
    vector<uint8_t> frame = py_bytearray((width * height));
    double aspect = py_div(width, height);
    double fov = 1.25;
    long long i = 0;
    auto __pytra_range_start_7 = 0;
    auto __pytra_range_stop_8 = height;
    auto __pytra_range_step_9 = 1;
    if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto py = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (py < __pytra_range_stop_8) : (py > __pytra_range_stop_8); py += __pytra_range_step_9)
    {
        double sy = (1.0 - py_div((2.0 * (py + 0.5)), height));
        auto __pytra_range_start_10 = 0;
        auto __pytra_range_stop_11 = width;
        auto __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto px = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (px < __pytra_range_stop_11) : (px > __pytra_range_stop_11); px += __pytra_range_step_12)
        {
            double sx = ((py_div((2.0 * (px + 0.5)), width) - 1.0) * aspect);
            auto rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))));
            auto ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))));
            auto rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))));
            auto __pytra_tuple_13 = normalize(rx, ry, rz);
            auto dx = std::get<0>(__pytra_tuple_13);
            auto dy = std::get<1>(__pytra_tuple_13);
            auto dz = std::get<2>(__pytra_tuple_13);
            double best_t = 1000000000.0;
            long long hit_kind = 0;
            double r = 0.0;
            double g = 0.0;
            double b = 0.0;
            if ((dy < (-1e-06)))
            {
                double tf = py_div(((-1.2) - cam_y), dy);
                if (((tf > 0.0001) && (tf < best_t)))
                {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            auto t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (((t0 > 0.0) && (t0 < best_t)))
            {
                best_t = t0;
                hit_kind = 2;
            }
            auto t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (((t1 > 0.0) && (t1 < best_t)))
            {
                best_t = t1;
                hit_kind = 3;
            }
            auto t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (((t2 > 0.0) && (t2 < best_t)))
            {
                best_t = t2;
                hit_kind = 4;
            }
            if ((hit_kind == 0))
            {
                auto __pytra_tuple_14 = sky_color(dx, dy, dz, tphase);
                r = std::get<0>(__pytra_tuple_14);
                g = std::get<1>(__pytra_tuple_14);
                b = std::get<2>(__pytra_tuple_14);
            }
            else
            {
                if ((hit_kind == 1))
                {
                    auto hx = (cam_x + (best_t * dx));
                    auto hz = (cam_z + (best_t * dz));
                    long long cx = static_cast<long long>(pycs::cpp_module::math::floor((hx * 2.0)));
                    long long cz = static_cast<long long>(pycs::cpp_module::math::floor((hz * 2.0)));
                    auto checker = ((((cx + cz) % 2) == 0) ? 0 : 1);
                    auto base_r = ((checker == 0) ? 0.1 : 0.04);
                    auto base_g = ((checker == 0) ? 0.11 : 0.05);
                    auto base_b = ((checker == 0) ? 0.13 : 0.08);
                    auto lxv = (lx - hx);
                    double lyv = (ly - (-1.2));
                    auto lzv = (lz - hz);
                    auto __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                    auto ldx = std::get<0>(__pytra_tuple_15);
                    auto ldy = std::get<1>(__pytra_tuple_15);
                    auto ldz = std::get<2>(__pytra_tuple_15);
                    auto ndotl = max(ldy, 0.0);
                    auto ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv));
                    double glow = py_div(8.0, (1.0 + ldist2));
                    r = ((base_r + (0.8 * glow)) + (0.2 * ndotl));
                    g = ((base_g + (0.5 * glow)) + (0.18 * ndotl));
                    b = ((base_b + (1.0 * glow)) + (0.24 * ndotl));
                }
                else
                {
                    double cx = 0.0;
                    double cy = 0.0;
                    double cz = 0.0;
                    double rad = 1.0;
                    if ((hit_kind == 2))
                    {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    }
                    else
                    {
                        if ((hit_kind == 3))
                        {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        }
                        else
                        {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    auto hx = (cam_x + (best_t * dx));
                    auto hy = (cam_y + (best_t * dy));
                    auto hz = (cam_z + (best_t * dz));
                    auto __pytra_tuple_16 = normalize(py_div((hx - cx), rad), py_div((hy - cy), rad), py_div((hz - cz), rad));
                    auto nx = std::get<0>(__pytra_tuple_16);
                    auto ny = std::get<1>(__pytra_tuple_16);
                    auto nz = std::get<2>(__pytra_tuple_16);
                    auto __pytra_tuple_17 = reflect(dx, dy, dz, nx, ny, nz);
                    auto rdx = std::get<0>(__pytra_tuple_17);
                    auto rdy = std::get<1>(__pytra_tuple_17);
                    auto rdz = std::get<2>(__pytra_tuple_17);
                    auto __pytra_tuple_18 = refract(dx, dy, dz, nx, ny, nz, py_div(1.0, 1.45));
                    auto tdx = std::get<0>(__pytra_tuple_18);
                    auto tdy = std::get<1>(__pytra_tuple_18);
                    auto tdz = std::get<2>(__pytra_tuple_18);
                    auto __pytra_tuple_19 = sky_color(rdx, rdy, rdz, tphase);
                    auto sr = std::get<0>(__pytra_tuple_19);
                    auto sg = std::get<1>(__pytra_tuple_19);
                    auto sb = std::get<2>(__pytra_tuple_19);
                    auto __pytra_tuple_20 = sky_color(tdx, tdy, tdz, (tphase + 0.8));
                    auto tr = std::get<0>(__pytra_tuple_20);
                    auto tg = std::get<1>(__pytra_tuple_20);
                    auto tb = std::get<2>(__pytra_tuple_20);
                    auto cosi = max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0);
                    auto fr = schlick(cosi, 0.04);
                    r = ((tr * (1.0 - fr)) + (sr * fr));
                    g = ((tg * (1.0 - fr)) + (sg * fr));
                    b = ((tb * (1.0 - fr)) + (sb * fr));
                    auto lxv = (lx - hx);
                    auto lyv = (ly - hy);
                    auto lzv = (lz - hz);
                    auto __pytra_tuple_21 = normalize(lxv, lyv, lzv);
                    auto ldx = std::get<0>(__pytra_tuple_21);
                    auto ldy = std::get<1>(__pytra_tuple_21);
                    auto ldz = std::get<2>(__pytra_tuple_21);
                    auto ndotl = max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0);
                    auto __pytra_tuple_22 = normalize((ldx - dx), (ldy - dy), (ldz - dz));
                    auto hvx = std::get<0>(__pytra_tuple_22);
                    auto hvy = std::get<1>(__pytra_tuple_22);
                    auto hvz = std::get<2>(__pytra_tuple_22);
                    auto ndoth = max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0);
                    auto spec = (ndoth * ndoth);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    double glow = py_div(10.0, (((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)));
                    r = (r + (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow)));
                    g = (g + (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow)));
                    b = (b + (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow)));
                    if ((hit_kind == 2))
                    {
                        r = (r * 0.95);
                        g = (g * 1.05);
                        b = (b * 1.1);
                    }
                    else
                    {
                        if ((hit_kind == 3))
                        {
                            r = (r * 1.08);
                            g = (g * 0.98);
                            b = (b * 1.04);
                        }
                        else
                        {
                            r = (r * 1.02);
                            g = (g * 1.1);
                            b = (b * 0.95);
                        }
                    }
                }
            }
            r = pycs::cpp_module::math::sqrt(clamp01(r));
            g = pycs::cpp_module::math::sqrt(clamp01(g));
            b = pycs::cpp_module::math::sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i = (i + 1);
        }
    }
    return py_bytes(frame);
}

void run_16_glass_sculpture_chaos()
{
    long long width = 320;
    long long height = 240;
    long long frames_n = 72;
    string out_path = "sample/out/16_glass_sculpture_chaos.gif";
    auto start = perf_counter();
    vector<vector<uint8_t>> frames = {};
    auto __pytra_range_start_23 = 0;
    auto __pytra_range_stop_24 = frames_n;
    auto __pytra_range_step_25 = 1;
    if (__pytra_range_step_25 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_23; (__pytra_range_step_25 > 0) ? (i < __pytra_range_stop_24) : (i > __pytra_range_stop_24); i += __pytra_range_step_25)
    {
        frames.push_back(render_frame(width, height, i, frames_n));
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_16_glass_sculpture_chaos();
    return 0;
}
```
</details>

<details>
<summary>Rustへの変換例 : 16_glass_sculpture_chaos.rs</summary>

```rust
#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_floor, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

// このファイルは自動生成です（native Rust mode）。

fn clamp01(mut v: f64) -> f64 {
    if py_bool(&(((v) < (0.0)))) {
        return 0.0;
    }
    if py_bool(&(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}

fn dot(mut ax: f64, mut ay: f64, mut az: f64, mut bx: f64, mut by: f64, mut bz: f64) -> f64 {
    return ((((((ax) * (bx))) + (((ay) * (by))))) + (((az) * (bz))));
}

fn length(mut x: f64, mut y: f64, mut z: f64) -> f64 {
    return math_sqrt(((((((((x) * (x))) + (((y) * (y))))) + (((z) * (z))))) as f64));
}

fn normalize(mut x: f64, mut y: f64, mut z: f64) -> (f64, f64, f64) {
    let mut l = length(x, y, z);
    if py_bool(&(((l) < (1e-09)))) {
        return (0.0, 0.0, 0.0);
    }
    return (((( x ) as f64) / (( l ) as f64)), ((( y ) as f64) / (( l ) as f64)), ((( z ) as f64) / (( l ) as f64)));
}

fn reflect(mut ix: f64, mut iy: f64, mut iz: f64, mut nx: f64, mut ny: f64, mut nz: f64) -> (f64, f64, f64) {
    let mut d = ((dot(ix, iy, iz, nx, ny, nz)) * (2.0));
    return (((ix) - (((d) * (nx)))), ((iy) - (((d) * (ny)))), ((iz) - (((d) * (nz)))));
}

fn refract(mut ix: f64, mut iy: f64, mut iz: f64, mut nx: f64, mut ny: f64, mut nz: f64, mut eta: f64) -> (f64, f64, f64) {
    let mut cosi = (-dot(ix, iy, iz, nx, ny, nz));
    let mut sint2 = ((((eta) * (eta))) * (((1.0) - (((cosi) * (cosi))))));
    if py_bool(&(((sint2) > (1.0)))) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let mut cost = math_sqrt(((((1.0) - (sint2))) as f64));
    let mut k = ((((eta) * (cosi))) - (cost));
    return (((((eta) * (ix))) + (((k) * (nx)))), ((((eta) * (iy))) + (((k) * (ny)))), ((((eta) * (iz))) + (((k) * (nz)))));
}

fn schlick(mut cos_theta: f64, mut f0: f64) -> f64 {
    let mut m = ((1.0) - (cos_theta));
    return ((f0) + (((((1.0) - (f0))) * (((((((((m) * (m))) * (m))) * (m))) * (m))))));
}

fn sky_color(mut dx: f64, mut dy: f64, mut dz: f64, mut tphase: f64) -> (f64, f64, f64) {
    let mut t = ((0.5) * (((dy) + (1.0))));
    let mut r = ((0.06) + (((0.2) * (t))));
    let mut g = ((0.1) + (((0.25) * (t))));
    let mut b = ((0.16) + (((0.45) * (t))));
    let mut band = ((0.5) + (((0.5) * (math_sin(((((((((8.0) * (dx))) + (((6.0) * (dz))))) + (tphase))) as f64))))));
    r = r + ((0.08) * (band));
    g = g + ((0.05) * (band));
    b = b + ((0.12) * (band));
    return (clamp01(r), clamp01(g), clamp01(b));
}

fn sphere_intersect(mut ox: f64, mut oy: f64, mut oz: f64, mut dx: f64, mut dy: f64, mut dz: f64, mut cx: f64, mut cy: f64, mut cz: f64, mut radius: f64) -> f64 {
    let mut lx = ((ox) - (cx));
    let mut ly = ((oy) - (cy));
    let mut lz = ((oz) - (cz));
    let mut b = ((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))));
    let mut c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((radius) * (radius))));
    let mut h = ((((b) * (b))) - (c));
    if py_bool(&(((h) < (0.0)))) {
        return (-1.0);
    }
    let mut s = math_sqrt(((h) as f64));
    let mut t0 = (((-b)) - (s));
    if py_bool(&(((t0) > (0.0001)))) {
        return t0;
    }
    let mut t1 = (((-b)) + (s));
    if py_bool(&(((t1) > (0.0001)))) {
        return t1;
    }
    return (-1.0);
}

fn palette_332() -> Vec<u8> {
    let mut p = vec![0u8; (((256) * (3))) as usize];
    for i in (0)..(256) {
        let mut r = ((((i) >> (5))) & (7));
        let mut g = ((((i) >> (2))) & (7));
        let mut b = ((i) & (3));
        (p)[((((i) * (3))) + (0)) as usize] = (((((( ((255) * (r)) ) as f64) / (( 7 ) as f64))) as i64)) as u8;
        (p)[((((i) * (3))) + (1)) as usize] = (((((( ((255) * (g)) ) as f64) / (( 7 ) as f64))) as i64)) as u8;
        (p)[((((i) * (3))) + (2)) as usize] = (((((( ((255) * (b)) ) as f64) / (( 3 ) as f64))) as i64)) as u8;
    }
    return (p).clone();
}

fn quantize_332(mut r: f64, mut g: f64, mut b: f64) -> i64 {
    let mut rr = ((((clamp01(r)) * (255.0))) as i64);
    let mut gg = ((((clamp01(g)) * (255.0))) as i64);
    let mut bb = ((((clamp01(b)) * (255.0))) as i64);
    return ((((((((rr) >> (5))) << (5))) + (((((gg) >> (5))) << (2))))) + (((bb) >> (6))));
}

fn render_frame(mut width: i64, mut height: i64, mut frame_id: i64, mut frames_n: i64) -> Vec<u8> {
    let mut t = ((( frame_id ) as f64) / (( frames_n ) as f64));
    let mut tphase = ((((2.0) * (std::f64::consts::PI))) * (t));
    let mut cam_r = 3.0;
    let mut cam_x = ((cam_r) * (math_cos(((((tphase) * (0.9))) as f64))));
    let mut cam_y = ((1.1) + (((0.25) * (math_sin(((((tphase) * (0.6))) as f64))))));
    let mut cam_z = ((cam_r) * (math_sin(((((tphase) * (0.9))) as f64))));
    let mut look_x = 0.0;
    let mut look_y = 0.35;
    let mut look_z = 0.0;
    let __pytra_tuple_rhs_1 = normalize(((look_x) - (cam_x)), ((look_y) - (cam_y)), ((look_z) - (cam_z)));
    let mut fwd_x = __pytra_tuple_rhs_1.0;
    let mut fwd_y = __pytra_tuple_rhs_1.1;
    let mut fwd_z = __pytra_tuple_rhs_1.2;
    let __pytra_tuple_rhs_2 = normalize(fwd_z, 0.0, (-fwd_x));
    let mut right_x = __pytra_tuple_rhs_2.0;
    let mut right_y = __pytra_tuple_rhs_2.1;
    let mut right_z = __pytra_tuple_rhs_2.2;
    let __pytra_tuple_rhs_3 = normalize(((((right_y) * (fwd_z))) - (((right_z) * (fwd_y)))), ((((right_z) * (fwd_x))) - (((right_x) * (fwd_z)))), ((((right_x) * (fwd_y))) - (((right_y) * (fwd_x)))));
    let mut up_x = __pytra_tuple_rhs_3.0;
    let mut up_y = __pytra_tuple_rhs_3.1;
    let mut up_z = __pytra_tuple_rhs_3.2;
    let mut s0x = ((0.9) * (math_cos(((((1.3) * (tphase))) as f64))));
    let mut s0y = ((0.15) + (((0.35) * (math_sin(((((1.7) * (tphase))) as f64))))));
    let mut s0z = ((0.9) * (math_sin(((((1.3) * (tphase))) as f64))));
    let mut s1x = ((1.2) * (math_cos(((((((1.3) * (tphase))) + (2.094))) as f64))));
    let mut s1y = ((0.1) + (((0.4) * (math_sin(((((((1.1) * (tphase))) + (0.8))) as f64))))));
    let mut s1z = ((1.2) * (math_sin(((((((1.3) * (tphase))) + (2.094))) as f64))));
    let mut s2x = ((1.0) * (math_cos(((((((1.3) * (tphase))) + (4.188))) as f64))));
    let mut s2y = ((0.2) + (((0.3) * (math_sin(((((((1.5) * (tphase))) + (1.9))) as f64))))));
    let mut s2z = ((1.0) * (math_sin(((((((1.3) * (tphase))) + (4.188))) as f64))));
    let mut lr = 0.35;
    let mut lx = ((2.4) * (math_cos(((((tphase) * (1.8))) as f64))));
    let mut ly = ((1.8) + (((0.8) * (math_sin(((((tphase) * (1.2))) as f64))))));
    let mut lz = ((2.4) * (math_sin(((((tphase) * (1.8))) as f64))));
    let mut frame = vec![0u8; (((width) * (height))) as usize];
    let mut aspect = ((( width ) as f64) / (( height ) as f64));
    let mut fov = 1.25;
    let mut i = 0;
    for py in (0)..(height) {
        let mut sy = ((1.0) - (((( ((2.0) * ((((( py ) as f64) + (( 0.5 ) as f64))))) ) as f64) / (( height ) as f64))));
        for px in (0)..(width) {
            let mut sx = ((((((( ((2.0) * ((((( px ) as f64) + (( 0.5 ) as f64))))) ) as f64) / (( width ) as f64))) - (1.0))) * (aspect));
            let mut rx = ((fwd_x) + (((fov) * (((((sx) * (right_x))) + (((sy) * (up_x))))))));
            let mut ry = ((fwd_y) + (((fov) * (((((sx) * (right_y))) + (((sy) * (up_y))))))));
            let mut rz = ((fwd_z) + (((fov) * (((((sx) * (right_z))) + (((sy) * (up_z))))))));
            let __pytra_tuple_rhs_4 = normalize(rx, ry, rz);
            let mut dx = __pytra_tuple_rhs_4.0;
            let mut dy = __pytra_tuple_rhs_4.1;
            let mut dz = __pytra_tuple_rhs_4.2;
            let mut best_t = 1000000000.0;
            let mut hit_kind = 0;
            let mut r = 0.0;
            let mut g = 0.0;
            let mut b = 0.0;
            if py_bool(&(((dy) < ((-1e-06))))) {
                let mut tf = ((( (((-1.2)) - (cam_y)) ) as f64) / (( dy ) as f64));
                if py_bool(&((((tf) > (0.0001)) && ((tf) < (best_t))))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let mut t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if py_bool(&((((t0) > (0.0)) && ((t0) < (best_t))))) {
                best_t = t0;
                hit_kind = 2;
            }
            let mut t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if py_bool(&((((t1) > (0.0)) && ((t1) < (best_t))))) {
                best_t = t1;
                hit_kind = 3;
            }
            let mut t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if py_bool(&((((t2) > (0.0)) && ((t2) < (best_t))))) {
                best_t = t2;
                hit_kind = 4;
            }
            if py_bool(&(((hit_kind) == (0)))) {
                let __pytra_tuple_rhs_5 = sky_color(dx, dy, dz, tphase);
                r = __pytra_tuple_rhs_5.0;
                g = __pytra_tuple_rhs_5.1;
                b = __pytra_tuple_rhs_5.2;
            } else {
                if py_bool(&(((hit_kind) == (1)))) {
                    let mut hx = ((cam_x) + (((best_t) * (dx))));
                    let mut hz = ((cam_z) + (((best_t) * (dz))));
                    let mut cx = ((math_floor(((((hx) * (2.0))) as f64))) as i64);
                    let mut cz = ((math_floor(((((hz) * (2.0))) as f64))) as i64);
                    let mut checker = (if py_bool(&(((((((cx) + (cz))) % (2))) == (0)))) { 0 } else { 1 });
                    let mut base_r = (if py_bool(&(((checker) == (0)))) { 0.1 } else { 0.04 });
                    let mut base_g = (if py_bool(&(((checker) == (0)))) { 0.11 } else { 0.05 });
                    let mut base_b = (if py_bool(&(((checker) == (0)))) { 0.13 } else { 0.08 });
                    let mut lxv = ((lx) - (hx));
                    let mut lyv = ((ly) - ((-1.2)));
                    let mut lzv = ((lz) - (hz));
                    let __pytra_tuple_rhs_6 = normalize(lxv, lyv, lzv);
                    let mut ldx = __pytra_tuple_rhs_6.0;
                    let mut ldy = __pytra_tuple_rhs_6.1;
                    let mut ldz = __pytra_tuple_rhs_6.2;
                    let mut ndotl = (if (ldy) > (0.0) { ldy } else { 0.0 });
                    let mut ldist2 = ((((((lxv) * (lxv))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))));
                    let mut glow = ((( 8.0 ) as f64) / (( ((1.0) + (ldist2)) ) as f64));
                    r = ((((base_r) + (((0.8) * (glow))))) + (((0.2) * (ndotl))));
                    g = ((((base_g) + (((0.5) * (glow))))) + (((0.18) * (ndotl))));
                    b = ((((base_b) + (((1.0) * (glow))))) + (((0.24) * (ndotl))));
                } else {
                    let mut cx = 0.0;
                    let mut cy = 0.0;
                    let mut cz = 0.0;
                    let mut rad = 1.0;
                    if py_bool(&(((hit_kind) == (2)))) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if py_bool(&(((hit_kind) == (3)))) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    let mut hx = ((cam_x) + (((best_t) * (dx))));
                    let mut hy = ((cam_y) + (((best_t) * (dy))));
                    let mut hz = ((cam_z) + (((best_t) * (dz))));
                    let __pytra_tuple_rhs_7 = normalize(((( ((hx) - (cx)) ) as f64) / (( rad ) as f64)), ((( ((hy) - (cy)) ) as f64) / (( rad ) as f64)), ((( ((hz) - (cz)) ) as f64) / (( rad ) as f64)));
                    let mut nx = __pytra_tuple_rhs_7.0;
                    let mut ny = __pytra_tuple_rhs_7.1;
                    let mut nz = __pytra_tuple_rhs_7.2;
                    let __pytra_tuple_rhs_8 = reflect(dx, dy, dz, nx, ny, nz);
                    let mut rdx = __pytra_tuple_rhs_8.0;
                    let mut rdy = __pytra_tuple_rhs_8.1;
                    let mut rdz = __pytra_tuple_rhs_8.2;
                    let __pytra_tuple_rhs_9 = refract(dx, dy, dz, nx, ny, nz, ((( 1.0 ) as f64) / (( 1.45 ) as f64)));
                    let mut tdx = __pytra_tuple_rhs_9.0;
                    let mut tdy = __pytra_tuple_rhs_9.1;
                    let mut tdz = __pytra_tuple_rhs_9.2;
                    let __pytra_tuple_rhs_10 = sky_color(rdx, rdy, rdz, tphase);
                    let mut sr = __pytra_tuple_rhs_10.0;
                    let mut sg = __pytra_tuple_rhs_10.1;
                    let mut sb = __pytra_tuple_rhs_10.2;
                    let __pytra_tuple_rhs_11 = sky_color(tdx, tdy, tdz, ((tphase) + (0.8)));
                    let mut tr = __pytra_tuple_rhs_11.0;
                    let mut tg = __pytra_tuple_rhs_11.1;
                    let mut tb = __pytra_tuple_rhs_11.2;
                    let mut cosi = (if ((-((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz)))))) > (0.0) { (-((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz))))) } else { 0.0 });
                    let mut fr = schlick(cosi, 0.04);
                    r = ((((tr) * (((1.0) - (fr))))) + (((sr) * (fr))));
                    g = ((((tg) * (((1.0) - (fr))))) + (((sg) * (fr))));
                    b = ((((tb) * (((1.0) - (fr))))) + (((sb) * (fr))));
                    let mut lxv = ((lx) - (hx));
                    let mut lyv = ((ly) - (hy));
                    let mut lzv = ((lz) - (hz));
                    let __pytra_tuple_rhs_12 = normalize(lxv, lyv, lzv);
                    let mut ldx = __pytra_tuple_rhs_12.0;
                    let mut ldy = __pytra_tuple_rhs_12.1;
                    let mut ldz = __pytra_tuple_rhs_12.2;
                    let mut ndotl = (if (((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz))))) > (0.0) { ((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz)))) } else { 0.0 });
                    let __pytra_tuple_rhs_13 = normalize(((ldx) - (dx)), ((ldy) - (dy)), ((ldz) - (dz)));
                    let mut hvx = __pytra_tuple_rhs_13.0;
                    let mut hvy = __pytra_tuple_rhs_13.1;
                    let mut hvz = __pytra_tuple_rhs_13.2;
                    let mut ndoth = (if (((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz))))) > (0.0) { ((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz)))) } else { 0.0 });
                    let mut spec = ((ndoth) * (ndoth));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    let mut glow = ((( 10.0 ) as f64) / (( ((((((1.0) + (((lxv) * (lxv))))) + (((lyv) * (lyv))))) + (((lzv) * (lzv)))) ) as f64));
                    r = r + ((((((0.2) * (ndotl))) + (((0.8) * (spec))))) + (((0.45) * (glow))));
                    g = g + ((((((0.18) * (ndotl))) + (((0.6) * (spec))))) + (((0.35) * (glow))));
                    b = b + ((((((0.26) * (ndotl))) + (((1.0) * (spec))))) + (((0.65) * (glow))));
                    if py_bool(&(((hit_kind) == (2)))) {
                        r = r * 0.95;
                        g = g * 1.05;
                        b = b * 1.1;
                    } else {
                        if py_bool(&(((hit_kind) == (3)))) {
                            r = r * 1.08;
                            g = g * 0.98;
                            b = b * 1.04;
                        } else {
                            r = r * 1.02;
                            g = g * 1.1;
                            b = b * 0.95;
                        }
                    }
                }
            }
            r = math_sqrt(((clamp01(r)) as f64));
            g = math_sqrt(((clamp01(g)) as f64));
            b = math_sqrt(((clamp01(b)) as f64));
            (frame)[i as usize] = (quantize_332(r, g, b)) as u8;
            i = i + 1;
        }
    }
    return (frame).clone();
}

fn run_16_glass_sculpture_chaos() -> () {
    let mut width = 320;
    let mut height = 240;
    let mut frames_n = 72;
    let mut out_path = "sample/out/16_glass_sculpture_chaos.gif".to_string();
    let mut start = perf_counter();
    let mut frames: Vec<Vec<u8>> = vec![];
    for i in (0)..(frames_n) {
        frames.push(render_frame(width, height, i, frames_n));
    }
    py_save_gif(&(out_path), width, height, &(frames), &(palette_332()), 6, 0);
    let mut elapsed = ((perf_counter()) - (start));
    println!("{} {}", "output:".to_string(), out_path);
    println!("{} {}", "frames:".to_string(), frames_n);
    println!("{} {}", "elapsed_sec:".to_string(), elapsed);
}

fn main() {
    run_16_glass_sculpture_chaos();
}
```
</details>

<details>
<summary>C#への変換例 : 16_glass_sculpture_chaos.cs</summary>

```csharp
using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static double clamp01(double v)
    {
        if (Pytra.CsModule.py_runtime.py_bool((v < 0.0)))
        {
            return 0.0;
        }
        if (Pytra.CsModule.py_runtime.py_bool((v > 1.0)))
        {
            return 1.0;
        }
        return v;
    }

    public static double dot(double ax, double ay, double az, double bx, double by, double bz)
    {
        return (((ax * bx) + (ay * by)) + (az * bz));
    }

    public static double length(double x, double y, double z)
    {
        return Math.Sqrt((((x * x) + (y * y)) + (z * z)));
    }

    public static Tuple<double, double, double> normalize(double x, double y, double z)
    {
        var l = length(x, y, z);
        if (Pytra.CsModule.py_runtime.py_bool((l < 1e-09)))
        {
            return Tuple.Create(0.0, 0.0, 0.0);
        }
        return Tuple.Create(((double)(x) / (double)(l)), ((double)(y) / (double)(l)), ((double)(z) / (double)(l)));
    }

    public static Tuple<double, double, double> reflect(double ix, double iy, double iz, double nx, double ny, double nz)
    {
        var d = (dot(ix, iy, iz, nx, ny, nz) * 2.0);
        return Tuple.Create((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)));
    }

    public static Tuple<double, double, double> refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
    {
        var cosi = (-dot(ix, iy, iz, nx, ny, nz));
        var sint2 = ((eta * eta) * (1.0 - (cosi * cosi)));
        if (Pytra.CsModule.py_runtime.py_bool((sint2 > 1.0)))
        {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        var cost = Math.Sqrt((1.0 - sint2));
        var k = ((eta * cosi) - cost);
        return Tuple.Create(((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)));
    }

    public static double schlick(double cos_theta, double f0)
    {
        var m = (1.0 - cos_theta);
        return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)));
    }

    public static Tuple<double, double, double> sky_color(double dx, double dy, double dz, double tphase)
    {
        var t = (0.5 * (dy + 1.0));
        var r = (0.06 + (0.2 * t));
        var g = (0.1 + (0.25 * t));
        var b = (0.16 + (0.45 * t));
        var band = (0.5 + (0.5 * Math.Sin((((8.0 * dx) + (6.0 * dz)) + tphase))));
        r = (r + (0.08 * band));
        g = (g + (0.05 * band));
        b = (b + (0.12 * band));
        return Tuple.Create(clamp01(r), clamp01(g), clamp01(b));
    }

    public static double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
    {
        var lx = (ox - cx);
        var ly = (oy - cy);
        var lz = (oz - cz);
        var b = (((lx * dx) + (ly * dy)) + (lz * dz));
        var c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius));
        var h = ((b * b) - c);
        if (Pytra.CsModule.py_runtime.py_bool((h < 0.0)))
        {
            return (-1.0);
        }
        var s = Math.Sqrt(h);
        var t0 = ((-b) - s);
        if (Pytra.CsModule.py_runtime.py_bool((t0 > 0.0001)))
        {
            return t0;
        }
        var t1 = ((-b) + s);
        if (Pytra.CsModule.py_runtime.py_bool((t1 > 0.0001)))
        {
            return t1;
        }
        return (-1.0);
    }

    public static List<byte> palette_332()
    {
        var p = Pytra.CsModule.py_runtime.py_bytearray((256L * 3L));
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = ((i >> (int)(5L)) & 7L);
            var g = ((i >> (int)(2L)) & 7L);
            var b = (i & 3L);
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 0L), (long)(((double)((255L * r)) / (double)(7L))));
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 1L), (long)(((double)((255L * g)) / (double)(7L))));
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 2L), (long)(((double)((255L * b)) / (double)(3L))));
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }

    public static long quantize_332(double r, double g, double b)
    {
        var rr = (long)((clamp01(r) * 255.0));
        var gg = (long)((clamp01(g) * 255.0));
        var bb = (long)((clamp01(b) * 255.0));
        return ((((rr >> (int)(5L)) << (int)(5L)) + ((gg >> (int)(5L)) << (int)(2L))) + (bb >> (int)(6L)));
    }

    public static List<byte> render_frame(long width, long height, long frame_id, long frames_n)
    {
        var t = ((double)(frame_id) / (double)(frames_n));
        var tphase = ((2.0 * Math.PI) * t);
        double cam_r = 3.0;
        var cam_x = (cam_r * Math.Cos((tphase * 0.9)));
        var cam_y = (1.1 + (0.25 * Math.Sin((tphase * 0.6))));
        var cam_z = (cam_r * Math.Sin((tphase * 0.9)));
        double look_x = 0.0;
        double look_y = 0.35;
        double look_z = 0.0;
        var __pytra_tuple_4 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z));
        var fwd_x = __pytra_tuple_4.Item1;
        var fwd_y = __pytra_tuple_4.Item2;
        var fwd_z = __pytra_tuple_4.Item3;
        var __pytra_tuple_5 = normalize(fwd_z, 0.0, (-fwd_x));
        var right_x = __pytra_tuple_5.Item1;
        var right_y = __pytra_tuple_5.Item2;
        var right_z = __pytra_tuple_5.Item3;
        var __pytra_tuple_6 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)));
        var up_x = __pytra_tuple_6.Item1;
        var up_y = __pytra_tuple_6.Item2;
        var up_z = __pytra_tuple_6.Item3;
        var s0x = (0.9 * Math.Cos((1.3 * tphase)));
        var s0y = (0.15 + (0.35 * Math.Sin((1.7 * tphase))));
        var s0z = (0.9 * Math.Sin((1.3 * tphase)));
        var s1x = (1.2 * Math.Cos(((1.3 * tphase) + 2.094)));
        var s1y = (0.1 + (0.4 * Math.Sin(((1.1 * tphase) + 0.8))));
        var s1z = (1.2 * Math.Sin(((1.3 * tphase) + 2.094)));
        var s2x = (1.0 * Math.Cos(((1.3 * tphase) + 4.188)));
        var s2y = (0.2 + (0.3 * Math.Sin(((1.5 * tphase) + 1.9))));
        var s2z = (1.0 * Math.Sin(((1.3 * tphase) + 4.188)));
        double lr = 0.35;
        var lx = (2.4 * Math.Cos((tphase * 1.8)));
        var ly = (1.8 + (0.8 * Math.Sin((tphase * 1.2))));
        var lz = (2.4 * Math.Sin((tphase * 1.8)));
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
        var aspect = ((double)(width) / (double)(height));
        double fov = 1.25;
        long i = 0L;
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = height;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var py = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (py < __pytra_range_stop_8) : (py > __pytra_range_stop_8); py += __pytra_range_step_9)
        {
            var sy = (1.0 - ((double)((2.0 * (py + 0.5))) / (double)(height)));
            var __pytra_range_start_10 = 0;
            var __pytra_range_stop_11 = width;
            var __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var px = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (px < __pytra_range_stop_11) : (px > __pytra_range_stop_11); px += __pytra_range_step_12)
            {
                var sx = ((((double)((2.0 * (px + 0.5))) / (double)(width)) - 1.0) * aspect);
                var rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))));
                var ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))));
                var rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))));
                var __pytra_tuple_13 = normalize(rx, ry, rz);
                var dx = __pytra_tuple_13.Item1;
                var dy = __pytra_tuple_13.Item2;
                var dz = __pytra_tuple_13.Item3;
                double best_t = 1000000000.0;
                long hit_kind = 0L;
                double r = 0.0;
                double g = 0.0;
                double b = 0.0;
                if (Pytra.CsModule.py_runtime.py_bool((dy < (-1e-06))))
                {
                    var tf = ((double)(((-1.2) - cam_y)) / (double)(dy));
                    if (Pytra.CsModule.py_runtime.py_bool(((tf > 0.0001) && (tf < best_t))))
                    {
                        best_t = tf;
                        hit_kind = 1L;
                    }
                }
                var t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if (Pytra.CsModule.py_runtime.py_bool(((t0 > 0.0) && (t0 < best_t))))
                {
                    best_t = t0;
                    hit_kind = 2L;
                }
                var t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if (Pytra.CsModule.py_runtime.py_bool(((t1 > 0.0) && (t1 < best_t))))
                {
                    best_t = t1;
                    hit_kind = 3L;
                }
                var t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if (Pytra.CsModule.py_runtime.py_bool(((t2 > 0.0) && (t2 < best_t))))
                {
                    best_t = t2;
                    hit_kind = 4L;
                }
                if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 0L)))
                {
                    var __pytra_tuple_14 = sky_color(dx, dy, dz, tphase);
                    r = __pytra_tuple_14.Item1;
                    g = __pytra_tuple_14.Item2;
                    b = __pytra_tuple_14.Item3;
                }
                else
                {
                    if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 1L)))
                    {
                        var hx = (cam_x + (best_t * dx));
                        var hz = (cam_z + (best_t * dz));
                        var cx = (long)(Math.Floor((hx * 2.0)));
                        var cz = (long)(Math.Floor((hz * 2.0)));
                        var checker = (Pytra.CsModule.py_runtime.py_bool((((cx + cz) % 2L) == 0L)) ? 0L : 1L);
                        var base_r = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.1 : 0.04);
                        var base_g = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.11 : 0.05);
                        var base_b = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.13 : 0.08);
                        var lxv = (lx - hx);
                        var lyv = (ly - (-1.2));
                        var lzv = (lz - hz);
                        var __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                        var ldx = __pytra_tuple_15.Item1;
                        var ldy = __pytra_tuple_15.Item2;
                        var ldz = __pytra_tuple_15.Item3;
                        var ndotl = ((ldy) > (0.0) ? (ldy) : (0.0));
                        var ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv));
                        var glow = ((double)(8.0) / (double)((1.0 + ldist2)));
                        r = ((base_r + (0.8 * glow)) + (0.2 * ndotl));
                        g = ((base_g + (0.5 * glow)) + (0.18 * ndotl));
                        b = ((base_b + (1.0 * glow)) + (0.24 * ndotl));
                    }
                    else
                    {
                        double cx = 0.0;
                        double cy = 0.0;
                        double cz = 0.0;
                        double rad = 1.0;
                        if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 2L)))
                        {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        }
                        else
                        {
                            if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 3L)))
                            {
                                cx = s1x;
                                cy = s1y;
                                cz = s1z;
                                rad = 0.72;
                            }
                            else
                            {
                                cx = s2x;
                                cy = s2y;
                                cz = s2z;
                                rad = 0.58;
                            }
                        }
                        var hx = (cam_x + (best_t * dx));
                        var hy = (cam_y + (best_t * dy));
                        var hz = (cam_z + (best_t * dz));
                        var __pytra_tuple_16 = normalize(((double)((hx - cx)) / (double)(rad)), ((double)((hy - cy)) / (double)(rad)), ((double)((hz - cz)) / (double)(rad)));
                        var nx = __pytra_tuple_16.Item1;
                        var ny = __pytra_tuple_16.Item2;
                        var nz = __pytra_tuple_16.Item3;
                        var __pytra_tuple_17 = reflect(dx, dy, dz, nx, ny, nz);
                        var rdx = __pytra_tuple_17.Item1;
                        var rdy = __pytra_tuple_17.Item2;
                        var rdz = __pytra_tuple_17.Item3;
                        var __pytra_tuple_18 = refract(dx, dy, dz, nx, ny, nz, ((double)(1.0) / (double)(1.45)));
                        var tdx = __pytra_tuple_18.Item1;
                        var tdy = __pytra_tuple_18.Item2;
                        var tdz = __pytra_tuple_18.Item3;
                        var __pytra_tuple_19 = sky_color(rdx, rdy, rdz, tphase);
                        var sr = __pytra_tuple_19.Item1;
                        var sg = __pytra_tuple_19.Item2;
                        var sb = __pytra_tuple_19.Item3;
                        var __pytra_tuple_20 = sky_color(tdx, tdy, tdz, (tphase + 0.8));
                        var tr = __pytra_tuple_20.Item1;
                        var tg = __pytra_tuple_20.Item2;
                        var tb = __pytra_tuple_20.Item3;
                        var cosi = (((-(((dx * nx) + (dy * ny)) + (dz * nz)))) > (0.0) ? ((-(((dx * nx) + (dy * ny)) + (dz * nz)))) : (0.0));
                        var fr = schlick(cosi, 0.04);
                        r = ((tr * (1.0 - fr)) + (sr * fr));
                        g = ((tg * (1.0 - fr)) + (sg * fr));
                        b = ((tb * (1.0 - fr)) + (sb * fr));
                        var lxv = (lx - hx);
                        var lyv = (ly - hy);
                        var lzv = (lz - hz);
                        var __pytra_tuple_21 = normalize(lxv, lyv, lzv);
                        var ldx = __pytra_tuple_21.Item1;
                        var ldy = __pytra_tuple_21.Item2;
                        var ldz = __pytra_tuple_21.Item3;
                        var ndotl = (((((nx * ldx) + (ny * ldy)) + (nz * ldz))) > (0.0) ? ((((nx * ldx) + (ny * ldy)) + (nz * ldz))) : (0.0));
                        var __pytra_tuple_22 = normalize((ldx - dx), (ldy - dy), (ldz - dz));
                        var hvx = __pytra_tuple_22.Item1;
                        var hvy = __pytra_tuple_22.Item2;
                        var hvz = __pytra_tuple_22.Item3;
                        var ndoth = (((((nx * hvx) + (ny * hvy)) + (nz * hvz))) > (0.0) ? ((((nx * hvx) + (ny * hvy)) + (nz * hvz))) : (0.0));
                        var spec = (ndoth * ndoth);
                        spec = (spec * spec);
                        spec = (spec * spec);
                        spec = (spec * spec);
                        var glow = ((double)(10.0) / (double)((((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv))));
                        r = (r + (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow)));
                        g = (g + (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow)));
                        b = (b + (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow)));
                        if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 2L)))
                        {
                            r = (r * 0.95);
                            g = (g * 1.05);
                            b = (b * 1.1);
                        }
                        else
                        {
                            if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 3L)))
                            {
                                r = (r * 1.08);
                                g = (g * 0.98);
                                b = (b * 1.04);
                            }
                            else
                            {
                                r = (r * 1.02);
                                g = (g * 1.1);
                                b = (b * 0.95);
                            }
                        }
                    }
                }
                r = Math.Sqrt(clamp01(r));
                g = Math.Sqrt(clamp01(g));
                b = Math.Sqrt(clamp01(b));
                Pytra.CsModule.py_runtime.py_set(frame, i, quantize_332(r, g, b));
                i = (i + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_16_glass_sculpture_chaos()
    {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        string out_path = "sample/out/16_glass_sculpture_chaos.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_23 = 0;
        var __pytra_range_stop_24 = frames_n;
        var __pytra_range_step_25 = 1;
        if (__pytra_range_step_25 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_23; (__pytra_range_step_25 > 0) ? (i < __pytra_range_stop_24) : (i > __pytra_range_stop_24); i += __pytra_range_step_25)
        {
            Pytra.CsModule.py_runtime.py_append(frames, render_frame(width, height, i, frames_n));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, palette_332(), delay_cs: 6L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_16_glass_sculpture_chaos();
    }
}
```
</details>

<details>
<summary>JavaScriptへの変換例 : 16_glass_sculpture_chaos.js</summary>

```javascript
// このファイルは自動生成です（Python -> JavaScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/js_module/py_runtime.js');
const py_math = require(__pytra_root + '/src/js_module/math.js');
const py_time = require(__pytra_root + '/src/js_module/time.js');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/js_module/math.js');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/js_module/gif_helper.js');

function clamp01(v) {
    if (pyBool(((v) < (0.0)))) {
        return 0.0;
    }
    if (pyBool(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}
function dot(ax, ay, az, bx, by, bz) {
    return ((((((ax) * (bx))) + (((ay) * (by))))) + (((az) * (bz))));
}
function length(x, y, z) {
    return math.sqrt(((((((x) * (x))) + (((y) * (y))))) + (((z) * (z)))));
}
function normalize(x, y, z) {
    let l = length(x, y, z);
    if (pyBool(((l) < (1e-09)))) {
        return [0.0, 0.0, 0.0];
    }
    return [((x) / (l)), ((y) / (l)), ((z) / (l))];
}
function reflect(ix, iy, iz, nx, ny, nz) {
    let d = ((dot(ix, iy, iz, nx, ny, nz)) * (2.0));
    return [((ix) - (((d) * (nx)))), ((iy) - (((d) * (ny)))), ((iz) - (((d) * (nz))))];
}
function refract(ix, iy, iz, nx, ny, nz, eta) {
    let cosi = (-(dot(ix, iy, iz, nx, ny, nz)));
    let sint2 = ((((eta) * (eta))) * (((1.0) - (((cosi) * (cosi))))));
    if (pyBool(((sint2) > (1.0)))) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math.sqrt(((1.0) - (sint2)));
    let k = ((((eta) * (cosi))) - (cost));
    return [((((eta) * (ix))) + (((k) * (nx)))), ((((eta) * (iy))) + (((k) * (ny)))), ((((eta) * (iz))) + (((k) * (nz))))];
}
function schlick(cos_theta, f0) {
    let m = ((1.0) - (cos_theta));
    return ((f0) + (((((1.0) - (f0))) * (((((((((m) * (m))) * (m))) * (m))) * (m))))));
}
function sky_color(dx, dy, dz, tphase) {
    let t = ((0.5) * (((dy) + (1.0))));
    let r = ((0.06) + (((0.2) * (t))));
    let g = ((0.1) + (((0.25) * (t))));
    let b = ((0.16) + (((0.45) * (t))));
    let band = ((0.5) + (((0.5) * (math.sin(((((((8.0) * (dx))) + (((6.0) * (dz))))) + (tphase)))))));
    r = r + ((0.08) * (band));
    g = g + ((0.05) * (band));
    b = b + ((0.12) * (band));
    return [clamp01(r), clamp01(g), clamp01(b)];
}
function sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius) {
    let lx = ((ox) - (cx));
    let ly = ((oy) - (cy));
    let lz = ((oz) - (cz));
    let b = ((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))));
    let c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((radius) * (radius))));
    let h = ((((b) * (b))) - (c));
    if (pyBool(((h) < (0.0)))) {
        return (-(1.0));
    }
    let s = math.sqrt(h);
    let t0 = (((-(b))) - (s));
    if (pyBool(((t0) > (0.0001)))) {
        return t0;
    }
    let t1 = (((-(b))) + (s));
    if (pyBool(((t1) > (0.0001)))) {
        return t1;
    }
    return (-(1.0));
}
function palette_332() {
    let p = pyBytearray(((256) * (3)));
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = ((((i) >> (5))) & (7));
        let g = ((((i) >> (2))) & (7));
        let b = ((i) & (3));
        p[((((i) * (3))) + (0))] = Math.trunc(Number(((((255) * (r))) / (7))));
        p[((((i) * (3))) + (1))] = Math.trunc(Number(((((255) * (g))) / (7))));
        p[((((i) * (3))) + (2))] = Math.trunc(Number(((((255) * (b))) / (3))));
    }
    return pyBytes(p);
}
function quantize_332(r, g, b) {
    let rr = Math.trunc(Number(((clamp01(r)) * (255.0))));
    let gg = Math.trunc(Number(((clamp01(g)) * (255.0))));
    let bb = Math.trunc(Number(((clamp01(b)) * (255.0))));
    return ((((((((rr) >> (5))) << (5))) + (((((gg) >> (5))) << (2))))) + (((bb) >> (6))));
}
function render_frame(width, height, frame_id, frames_n) {
    let t = ((frame_id) / (frames_n));
    let tphase = ((((2.0) * (math.pi))) * (t));
    let cam_r = 3.0;
    let cam_x = ((cam_r) * (math.cos(((tphase) * (0.9)))));
    let cam_y = ((1.1) + (((0.25) * (math.sin(((tphase) * (0.6)))))));
    let cam_z = ((cam_r) * (math.sin(((tphase) * (0.9)))));
    let look_x = 0.0;
    let look_y = 0.35;
    let look_z = 0.0;
    const __pytra_tuple_2 = normalize(((look_x) - (cam_x)), ((look_y) - (cam_y)), ((look_z) - (cam_z)));
    let fwd_x = __pytra_tuple_2[0];
    let fwd_y = __pytra_tuple_2[1];
    let fwd_z = __pytra_tuple_2[2];
    const __pytra_tuple_3 = normalize(fwd_z, 0.0, (-(fwd_x)));
    let right_x = __pytra_tuple_3[0];
    let right_y = __pytra_tuple_3[1];
    let right_z = __pytra_tuple_3[2];
    const __pytra_tuple_4 = normalize(((((right_y) * (fwd_z))) - (((right_z) * (fwd_y)))), ((((right_z) * (fwd_x))) - (((right_x) * (fwd_z)))), ((((right_x) * (fwd_y))) - (((right_y) * (fwd_x)))));
    let up_x = __pytra_tuple_4[0];
    let up_y = __pytra_tuple_4[1];
    let up_z = __pytra_tuple_4[2];
    let s0x = ((0.9) * (math.cos(((1.3) * (tphase)))));
    let s0y = ((0.15) + (((0.35) * (math.sin(((1.7) * (tphase)))))));
    let s0z = ((0.9) * (math.sin(((1.3) * (tphase)))));
    let s1x = ((1.2) * (math.cos(((((1.3) * (tphase))) + (2.094)))));
    let s1y = ((0.1) + (((0.4) * (math.sin(((((1.1) * (tphase))) + (0.8)))))));
    let s1z = ((1.2) * (math.sin(((((1.3) * (tphase))) + (2.094)))));
    let s2x = ((1.0) * (math.cos(((((1.3) * (tphase))) + (4.188)))));
    let s2y = ((0.2) + (((0.3) * (math.sin(((((1.5) * (tphase))) + (1.9)))))));
    let s2z = ((1.0) * (math.sin(((((1.3) * (tphase))) + (4.188)))));
    let lr = 0.35;
    let lx = ((2.4) * (math.cos(((tphase) * (1.8)))));
    let ly = ((1.8) + (((0.8) * (math.sin(((tphase) * (1.2)))))));
    let lz = ((2.4) * (math.sin(((tphase) * (1.8)))));
    let frame = pyBytearray(((width) * (height)));
    let aspect = ((width) / (height));
    let fov = 1.25;
    let i = 0;
    let py;
    for (let __pytra_i_5 = 0; __pytra_i_5 < height; __pytra_i_5 += 1) {
        py = __pytra_i_5;
        let sy = ((1.0) - (((((2.0) * (((py) + (0.5))))) / (height))));
        let px;
        for (let __pytra_i_6 = 0; __pytra_i_6 < width; __pytra_i_6 += 1) {
            px = __pytra_i_6;
            let sx = ((((((((2.0) * (((px) + (0.5))))) / (width))) - (1.0))) * (aspect));
            let rx = ((fwd_x) + (((fov) * (((((sx) * (right_x))) + (((sy) * (up_x))))))));
            let ry = ((fwd_y) + (((fov) * (((((sx) * (right_y))) + (((sy) * (up_y))))))));
            let rz = ((fwd_z) + (((fov) * (((((sx) * (right_z))) + (((sy) * (up_z))))))));
            const __pytra_tuple_7 = normalize(rx, ry, rz);
            let dx = __pytra_tuple_7[0];
            let dy = __pytra_tuple_7[1];
            let dz = __pytra_tuple_7[2];
            let best_t = 1000000000.0;
            let hit_kind = 0;
            let r = 0.0;
            let g = 0.0;
            let b = 0.0;
            if (pyBool(((dy) < ((-(1e-06)))))) {
                let tf = (((((-(1.2))) - (cam_y))) / (dy));
                if (pyBool((((tf) > (0.0001)) && ((tf) < (best_t))))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (pyBool((((t0) > (0.0)) && ((t0) < (best_t))))) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (pyBool((((t1) > (0.0)) && ((t1) < (best_t))))) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (pyBool((((t2) > (0.0)) && ((t2) < (best_t))))) {
                best_t = t2;
                hit_kind = 4;
            }
            if (pyBool(((hit_kind) === (0)))) {
                const __pytra_tuple_8 = sky_color(dx, dy, dz, tphase);
                r = __pytra_tuple_8[0];
                g = __pytra_tuple_8[1];
                b = __pytra_tuple_8[2];
            } else {
                if (pyBool(((hit_kind) === (1)))) {
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    let cx = Math.trunc(Number(math.floor(((hx) * (2.0)))));
                    let cz = Math.trunc(Number(math.floor(((hz) * (2.0)))));
                    let checker = (pyBool(((pyMod(((cx) + (cz)), 2)) === (0))) ? 0 : 1);
                    let base_r = (pyBool(((checker) === (0))) ? 0.1 : 0.04);
                    let base_g = (pyBool(((checker) === (0))) ? 0.11 : 0.05);
                    let base_b = (pyBool(((checker) === (0))) ? 0.13 : 0.08);
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - ((-(1.2))));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_9 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_9[0];
                    let ldy = __pytra_tuple_9[1];
                    let ldz = __pytra_tuple_9[2];
                    let ndotl = Math.max(ldy, 0.0);
                    let ldist2 = ((((((lxv) * (lxv))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))));
                    let glow = ((8.0) / (((1.0) + (ldist2))));
                    r = ((((base_r) + (((0.8) * (glow))))) + (((0.2) * (ndotl))));
                    g = ((((base_g) + (((0.5) * (glow))))) + (((0.18) * (ndotl))));
                    b = ((((base_b) + (((1.0) * (glow))))) + (((0.24) * (ndotl))));
                } else {
                    let cx = 0.0;
                    let cy = 0.0;
                    let cz = 0.0;
                    let rad = 1.0;
                    if (pyBool(((hit_kind) === (2)))) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hy = ((cam_y) + (((best_t) * (dy))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    const __pytra_tuple_10 = normalize(((((hx) - (cx))) / (rad)), ((((hy) - (cy))) / (rad)), ((((hz) - (cz))) / (rad)));
                    let nx = __pytra_tuple_10[0];
                    let ny = __pytra_tuple_10[1];
                    let nz = __pytra_tuple_10[2];
                    const __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz);
                    let rdx = __pytra_tuple_11[0];
                    let rdy = __pytra_tuple_11[1];
                    let rdz = __pytra_tuple_11[2];
                    const __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, ((1.0) / (1.45)));
                    let tdx = __pytra_tuple_12[0];
                    let tdy = __pytra_tuple_12[1];
                    let tdz = __pytra_tuple_12[2];
                    const __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase);
                    let sr = __pytra_tuple_13[0];
                    let sg = __pytra_tuple_13[1];
                    let sb = __pytra_tuple_13[2];
                    const __pytra_tuple_14 = sky_color(tdx, tdy, tdz, ((tphase) + (0.8)));
                    let tr = __pytra_tuple_14[0];
                    let tg = __pytra_tuple_14[1];
                    let tb = __pytra_tuple_14[2];
                    let cosi = Math.max((-(((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz)))))), 0.0);
                    let fr = schlick(cosi, 0.04);
                    r = ((((tr) * (((1.0) - (fr))))) + (((sr) * (fr))));
                    g = ((((tg) * (((1.0) - (fr))))) + (((sg) * (fr))));
                    b = ((((tb) * (((1.0) - (fr))))) + (((sb) * (fr))));
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - (hy));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_15[0];
                    let ldy = __pytra_tuple_15[1];
                    let ldz = __pytra_tuple_15[2];
                    let ndotl = Math.max(((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz)))), 0.0);
                    const __pytra_tuple_16 = normalize(((ldx) - (dx)), ((ldy) - (dy)), ((ldz) - (dz)));
                    let hvx = __pytra_tuple_16[0];
                    let hvy = __pytra_tuple_16[1];
                    let hvz = __pytra_tuple_16[2];
                    let ndoth = Math.max(((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz)))), 0.0);
                    let spec = ((ndoth) * (ndoth));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    let glow = ((10.0) / (((((((1.0) + (((lxv) * (lxv))))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))))));
                    r = r + ((((((0.2) * (ndotl))) + (((0.8) * (spec))))) + (((0.45) * (glow))));
                    g = g + ((((((0.18) * (ndotl))) + (((0.6) * (spec))))) + (((0.35) * (glow))));
                    b = b + ((((((0.26) * (ndotl))) + (((1.0) * (spec))))) + (((0.65) * (glow))));
                    if (pyBool(((hit_kind) === (2)))) {
                        r = r * 0.95;
                        g = g * 1.05;
                        b = b * 1.1;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
                            r = r * 1.08;
                            g = g * 0.98;
                            b = b * 1.04;
                        } else {
                            r = r * 1.02;
                            g = g * 1.1;
                            b = b * 0.95;
                        }
                    }
                }
            }
            r = math.sqrt(clamp01(r));
            g = math.sqrt(clamp01(g));
            b = math.sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i = i + 1;
        }
    }
    return pyBytes(frame);
}
function run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = 'sample/out/16_glass_sculpture_chaos.gif';
    let start = perf_counter();
    let frames = [];
    let i;
    for (let __pytra_i_17 = 0; __pytra_i_17 < frames_n; __pytra_i_17 += 1) {
        i = __pytra_i_17;
        frames.push(render_frame(width, height, i, frames_n));
    }
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_16_glass_sculpture_chaos();
```
</details>

<details>
<summary>TypeScriptへの変換例 : 16_glass_sculpture_chaos.ts</summary>

```typescript
// このファイルは自動生成です（Python -> TypeScript native mode）。

const __pytra_root = process.cwd();
const py_runtime = require(__pytra_root + '/src/ts_module/py_runtime.ts');
const py_math = require(__pytra_root + '/src/ts_module/math.ts');
const py_time = require(__pytra_root + '/src/ts_module/time.ts');
const { pyPrint, pyLen, pyBool, pyRange, pyFloorDiv, pyMod, pyIn, pySlice, pyOrd, pyChr, pyBytearray, pyBytes, pyIsDigit, pyIsAlpha } = py_runtime;
const { perfCounter } = py_time;
const math = require(__pytra_root + '/src/ts_module/math.ts');
const perf_counter = perfCounter;
const { save_gif } = require(__pytra_root + '/src/ts_module/gif_helper.ts');

function clamp01(v) {
    if (pyBool(((v) < (0.0)))) {
        return 0.0;
    }
    if (pyBool(((v) > (1.0)))) {
        return 1.0;
    }
    return v;
}
function dot(ax, ay, az, bx, by, bz) {
    return ((((((ax) * (bx))) + (((ay) * (by))))) + (((az) * (bz))));
}
function length(x, y, z) {
    return math.sqrt(((((((x) * (x))) + (((y) * (y))))) + (((z) * (z)))));
}
function normalize(x, y, z) {
    let l = length(x, y, z);
    if (pyBool(((l) < (1e-09)))) {
        return [0.0, 0.0, 0.0];
    }
    return [((x) / (l)), ((y) / (l)), ((z) / (l))];
}
function reflect(ix, iy, iz, nx, ny, nz) {
    let d = ((dot(ix, iy, iz, nx, ny, nz)) * (2.0));
    return [((ix) - (((d) * (nx)))), ((iy) - (((d) * (ny)))), ((iz) - (((d) * (nz))))];
}
function refract(ix, iy, iz, nx, ny, nz, eta) {
    let cosi = (-(dot(ix, iy, iz, nx, ny, nz)));
    let sint2 = ((((eta) * (eta))) * (((1.0) - (((cosi) * (cosi))))));
    if (pyBool(((sint2) > (1.0)))) {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    let cost = math.sqrt(((1.0) - (sint2)));
    let k = ((((eta) * (cosi))) - (cost));
    return [((((eta) * (ix))) + (((k) * (nx)))), ((((eta) * (iy))) + (((k) * (ny)))), ((((eta) * (iz))) + (((k) * (nz))))];
}
function schlick(cos_theta, f0) {
    let m = ((1.0) - (cos_theta));
    return ((f0) + (((((1.0) - (f0))) * (((((((((m) * (m))) * (m))) * (m))) * (m))))));
}
function sky_color(dx, dy, dz, tphase) {
    let t = ((0.5) * (((dy) + (1.0))));
    let r = ((0.06) + (((0.2) * (t))));
    let g = ((0.1) + (((0.25) * (t))));
    let b = ((0.16) + (((0.45) * (t))));
    let band = ((0.5) + (((0.5) * (math.sin(((((((8.0) * (dx))) + (((6.0) * (dz))))) + (tphase)))))));
    r = r + ((0.08) * (band));
    g = g + ((0.05) * (band));
    b = b + ((0.12) * (band));
    return [clamp01(r), clamp01(g), clamp01(b)];
}
function sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius) {
    let lx = ((ox) - (cx));
    let ly = ((oy) - (cy));
    let lz = ((oz) - (cz));
    let b = ((((((lx) * (dx))) + (((ly) * (dy))))) + (((lz) * (dz))));
    let c = ((((((((lx) * (lx))) + (((ly) * (ly))))) + (((lz) * (lz))))) - (((radius) * (radius))));
    let h = ((((b) * (b))) - (c));
    if (pyBool(((h) < (0.0)))) {
        return (-(1.0));
    }
    let s = math.sqrt(h);
    let t0 = (((-(b))) - (s));
    if (pyBool(((t0) > (0.0001)))) {
        return t0;
    }
    let t1 = (((-(b))) + (s));
    if (pyBool(((t1) > (0.0001)))) {
        return t1;
    }
    return (-(1.0));
}
function palette_332() {
    let p = pyBytearray(((256) * (3)));
    let i;
    for (let __pytra_i_1 = 0; __pytra_i_1 < 256; __pytra_i_1 += 1) {
        i = __pytra_i_1;
        let r = ((((i) >> (5))) & (7));
        let g = ((((i) >> (2))) & (7));
        let b = ((i) & (3));
        p[((((i) * (3))) + (0))] = Math.trunc(Number(((((255) * (r))) / (7))));
        p[((((i) * (3))) + (1))] = Math.trunc(Number(((((255) * (g))) / (7))));
        p[((((i) * (3))) + (2))] = Math.trunc(Number(((((255) * (b))) / (3))));
    }
    return pyBytes(p);
}
function quantize_332(r, g, b) {
    let rr = Math.trunc(Number(((clamp01(r)) * (255.0))));
    let gg = Math.trunc(Number(((clamp01(g)) * (255.0))));
    let bb = Math.trunc(Number(((clamp01(b)) * (255.0))));
    return ((((((((rr) >> (5))) << (5))) + (((((gg) >> (5))) << (2))))) + (((bb) >> (6))));
}
function render_frame(width, height, frame_id, frames_n) {
    let t = ((frame_id) / (frames_n));
    let tphase = ((((2.0) * (math.pi))) * (t));
    let cam_r = 3.0;
    let cam_x = ((cam_r) * (math.cos(((tphase) * (0.9)))));
    let cam_y = ((1.1) + (((0.25) * (math.sin(((tphase) * (0.6)))))));
    let cam_z = ((cam_r) * (math.sin(((tphase) * (0.9)))));
    let look_x = 0.0;
    let look_y = 0.35;
    let look_z = 0.0;
    const __pytra_tuple_2 = normalize(((look_x) - (cam_x)), ((look_y) - (cam_y)), ((look_z) - (cam_z)));
    let fwd_x = __pytra_tuple_2[0];
    let fwd_y = __pytra_tuple_2[1];
    let fwd_z = __pytra_tuple_2[2];
    const __pytra_tuple_3 = normalize(fwd_z, 0.0, (-(fwd_x)));
    let right_x = __pytra_tuple_3[0];
    let right_y = __pytra_tuple_3[1];
    let right_z = __pytra_tuple_3[2];
    const __pytra_tuple_4 = normalize(((((right_y) * (fwd_z))) - (((right_z) * (fwd_y)))), ((((right_z) * (fwd_x))) - (((right_x) * (fwd_z)))), ((((right_x) * (fwd_y))) - (((right_y) * (fwd_x)))));
    let up_x = __pytra_tuple_4[0];
    let up_y = __pytra_tuple_4[1];
    let up_z = __pytra_tuple_4[2];
    let s0x = ((0.9) * (math.cos(((1.3) * (tphase)))));
    let s0y = ((0.15) + (((0.35) * (math.sin(((1.7) * (tphase)))))));
    let s0z = ((0.9) * (math.sin(((1.3) * (tphase)))));
    let s1x = ((1.2) * (math.cos(((((1.3) * (tphase))) + (2.094)))));
    let s1y = ((0.1) + (((0.4) * (math.sin(((((1.1) * (tphase))) + (0.8)))))));
    let s1z = ((1.2) * (math.sin(((((1.3) * (tphase))) + (2.094)))));
    let s2x = ((1.0) * (math.cos(((((1.3) * (tphase))) + (4.188)))));
    let s2y = ((0.2) + (((0.3) * (math.sin(((((1.5) * (tphase))) + (1.9)))))));
    let s2z = ((1.0) * (math.sin(((((1.3) * (tphase))) + (4.188)))));
    let lr = 0.35;
    let lx = ((2.4) * (math.cos(((tphase) * (1.8)))));
    let ly = ((1.8) + (((0.8) * (math.sin(((tphase) * (1.2)))))));
    let lz = ((2.4) * (math.sin(((tphase) * (1.8)))));
    let frame = pyBytearray(((width) * (height)));
    let aspect = ((width) / (height));
    let fov = 1.25;
    let i = 0;
    let py;
    for (let __pytra_i_5 = 0; __pytra_i_5 < height; __pytra_i_5 += 1) {
        py = __pytra_i_5;
        let sy = ((1.0) - (((((2.0) * (((py) + (0.5))))) / (height))));
        let px;
        for (let __pytra_i_6 = 0; __pytra_i_6 < width; __pytra_i_6 += 1) {
            px = __pytra_i_6;
            let sx = ((((((((2.0) * (((px) + (0.5))))) / (width))) - (1.0))) * (aspect));
            let rx = ((fwd_x) + (((fov) * (((((sx) * (right_x))) + (((sy) * (up_x))))))));
            let ry = ((fwd_y) + (((fov) * (((((sx) * (right_y))) + (((sy) * (up_y))))))));
            let rz = ((fwd_z) + (((fov) * (((((sx) * (right_z))) + (((sy) * (up_z))))))));
            const __pytra_tuple_7 = normalize(rx, ry, rz);
            let dx = __pytra_tuple_7[0];
            let dy = __pytra_tuple_7[1];
            let dz = __pytra_tuple_7[2];
            let best_t = 1000000000.0;
            let hit_kind = 0;
            let r = 0.0;
            let g = 0.0;
            let b = 0.0;
            if (pyBool(((dy) < ((-(1e-06)))))) {
                let tf = (((((-(1.2))) - (cam_y))) / (dy));
                if (pyBool((((tf) > (0.0001)) && ((tf) < (best_t))))) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            let t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (pyBool((((t0) > (0.0)) && ((t0) < (best_t))))) {
                best_t = t0;
                hit_kind = 2;
            }
            let t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (pyBool((((t1) > (0.0)) && ((t1) < (best_t))))) {
                best_t = t1;
                hit_kind = 3;
            }
            let t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (pyBool((((t2) > (0.0)) && ((t2) < (best_t))))) {
                best_t = t2;
                hit_kind = 4;
            }
            if (pyBool(((hit_kind) === (0)))) {
                const __pytra_tuple_8 = sky_color(dx, dy, dz, tphase);
                r = __pytra_tuple_8[0];
                g = __pytra_tuple_8[1];
                b = __pytra_tuple_8[2];
            } else {
                if (pyBool(((hit_kind) === (1)))) {
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    let cx = Math.trunc(Number(math.floor(((hx) * (2.0)))));
                    let cz = Math.trunc(Number(math.floor(((hz) * (2.0)))));
                    let checker = (pyBool(((pyMod(((cx) + (cz)), 2)) === (0))) ? 0 : 1);
                    let base_r = (pyBool(((checker) === (0))) ? 0.1 : 0.04);
                    let base_g = (pyBool(((checker) === (0))) ? 0.11 : 0.05);
                    let base_b = (pyBool(((checker) === (0))) ? 0.13 : 0.08);
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - ((-(1.2))));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_9 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_9[0];
                    let ldy = __pytra_tuple_9[1];
                    let ldz = __pytra_tuple_9[2];
                    let ndotl = Math.max(ldy, 0.0);
                    let ldist2 = ((((((lxv) * (lxv))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))));
                    let glow = ((8.0) / (((1.0) + (ldist2))));
                    r = ((((base_r) + (((0.8) * (glow))))) + (((0.2) * (ndotl))));
                    g = ((((base_g) + (((0.5) * (glow))))) + (((0.18) * (ndotl))));
                    b = ((((base_b) + (((1.0) * (glow))))) + (((0.24) * (ndotl))));
                } else {
                    let cx = 0.0;
                    let cy = 0.0;
                    let cz = 0.0;
                    let rad = 1.0;
                    if (pyBool(((hit_kind) === (2)))) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    let hx = ((cam_x) + (((best_t) * (dx))));
                    let hy = ((cam_y) + (((best_t) * (dy))));
                    let hz = ((cam_z) + (((best_t) * (dz))));
                    const __pytra_tuple_10 = normalize(((((hx) - (cx))) / (rad)), ((((hy) - (cy))) / (rad)), ((((hz) - (cz))) / (rad)));
                    let nx = __pytra_tuple_10[0];
                    let ny = __pytra_tuple_10[1];
                    let nz = __pytra_tuple_10[2];
                    const __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz);
                    let rdx = __pytra_tuple_11[0];
                    let rdy = __pytra_tuple_11[1];
                    let rdz = __pytra_tuple_11[2];
                    const __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, ((1.0) / (1.45)));
                    let tdx = __pytra_tuple_12[0];
                    let tdy = __pytra_tuple_12[1];
                    let tdz = __pytra_tuple_12[2];
                    const __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase);
                    let sr = __pytra_tuple_13[0];
                    let sg = __pytra_tuple_13[1];
                    let sb = __pytra_tuple_13[2];
                    const __pytra_tuple_14 = sky_color(tdx, tdy, tdz, ((tphase) + (0.8)));
                    let tr = __pytra_tuple_14[0];
                    let tg = __pytra_tuple_14[1];
                    let tb = __pytra_tuple_14[2];
                    let cosi = Math.max((-(((((((dx) * (nx))) + (((dy) * (ny))))) + (((dz) * (nz)))))), 0.0);
                    let fr = schlick(cosi, 0.04);
                    r = ((((tr) * (((1.0) - (fr))))) + (((sr) * (fr))));
                    g = ((((tg) * (((1.0) - (fr))))) + (((sg) * (fr))));
                    b = ((((tb) * (((1.0) - (fr))))) + (((sb) * (fr))));
                    let lxv = ((lx) - (hx));
                    let lyv = ((ly) - (hy));
                    let lzv = ((lz) - (hz));
                    const __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                    let ldx = __pytra_tuple_15[0];
                    let ldy = __pytra_tuple_15[1];
                    let ldz = __pytra_tuple_15[2];
                    let ndotl = Math.max(((((((nx) * (ldx))) + (((ny) * (ldy))))) + (((nz) * (ldz)))), 0.0);
                    const __pytra_tuple_16 = normalize(((ldx) - (dx)), ((ldy) - (dy)), ((ldz) - (dz)));
                    let hvx = __pytra_tuple_16[0];
                    let hvy = __pytra_tuple_16[1];
                    let hvz = __pytra_tuple_16[2];
                    let ndoth = Math.max(((((((nx) * (hvx))) + (((ny) * (hvy))))) + (((nz) * (hvz)))), 0.0);
                    let spec = ((ndoth) * (ndoth));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    spec = ((spec) * (spec));
                    let glow = ((10.0) / (((((((1.0) + (((lxv) * (lxv))))) + (((lyv) * (lyv))))) + (((lzv) * (lzv))))));
                    r = r + ((((((0.2) * (ndotl))) + (((0.8) * (spec))))) + (((0.45) * (glow))));
                    g = g + ((((((0.18) * (ndotl))) + (((0.6) * (spec))))) + (((0.35) * (glow))));
                    b = b + ((((((0.26) * (ndotl))) + (((1.0) * (spec))))) + (((0.65) * (glow))));
                    if (pyBool(((hit_kind) === (2)))) {
                        r = r * 0.95;
                        g = g * 1.05;
                        b = b * 1.1;
                    } else {
                        if (pyBool(((hit_kind) === (3)))) {
                            r = r * 1.08;
                            g = g * 0.98;
                            b = b * 1.04;
                        } else {
                            r = r * 1.02;
                            g = g * 1.1;
                            b = b * 0.95;
                        }
                    }
                }
            }
            r = math.sqrt(clamp01(r));
            g = math.sqrt(clamp01(g));
            b = math.sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i = i + 1;
        }
    }
    return pyBytes(frame);
}
function run_16_glass_sculpture_chaos() {
    let width = 320;
    let height = 240;
    let frames_n = 72;
    let out_path = 'sample/out/16_glass_sculpture_chaos.gif';
    let start = perf_counter();
    let frames = [];
    let i;
    for (let __pytra_i_17 = 0; __pytra_i_17 < frames_n; __pytra_i_17 += 1) {
        i = __pytra_i_17;
        frames.push(render_frame(width, height, i, frames_n));
    }
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    let elapsed = ((perf_counter()) - (start));
    pyPrint('output:', out_path);
    pyPrint('frames:', frames_n);
    pyPrint('elapsed_sec:', elapsed);
}
run_16_glass_sculpture_chaos();
```
</details>

<details>
<summary>Goへの変換例 : 16_glass_sculpture_chaos.go</summary>

```go
// このファイルは自動生成です（Python -> Go native mode）。

// Go ネイティブ変換向け Python 互換ランタイム補助。

package main

import (
    "bytes"
    "compress/zlib"
    "fmt"
    "hash/crc32"
    "math"
    "os"
    "strconv"
    "strings"
    "time"
)

func pyToString(v any) string {
    switch x := v.(type) {
    case nil:
        return "None"
    case bool:
        if x {
            return "True"
        }
        return "False"
    case string:
        return x
    case int:
        return strconv.Itoa(x)
    case int64:
        return strconv.FormatInt(x, 10)
    case float64:
        return strconv.FormatFloat(x, 'f', -1, 64)
    case []any:
        parts := make([]string, 0, len(x))
        for _, it := range x {
            parts = append(parts, pyToString(it))
        }
        return "[" + strings.Join(parts, ", ") + "]"
    case map[any]any:
        parts := make([]string, 0, len(x))
        for k, v := range x {
            parts = append(parts, pyToString(k)+": "+pyToString(v))
        }
        return "{" + strings.Join(parts, ", ") + "}"
    default:
        return fmt.Sprint(x)
    }
}

func pyPrint(args ...any) {
    parts := make([]string, 0, len(args))
    for _, a := range args {
        parts = append(parts, pyToString(a))
    }
    fmt.Println(strings.Join(parts, " "))
}

func pyBool(v any) bool {
    switch x := v.(type) {
    case nil:
        return false
    case bool:
        return x
    case int:
        return x != 0
    case int64:
        return x != 0
    case float64:
        return x != 0.0
    case string:
        return x != ""
    case []any:
        return len(x) > 0
    case []byte:
        return len(x) > 0
    case map[any]any:
        return len(x) > 0
    default:
        return true
    }
}

func pyLen(v any) int {
    switch x := v.(type) {
    case string:
        return len([]rune(x))
    case []any:
        return len(x)
    case []byte:
        return len(x)
    case map[any]any:
        return len(x)
    default:
        panic("len() unsupported type")
    }
}

func pyRange(start, stop, step int) []any {
    if step == 0 {
        panic("range() step must not be zero")
    }
    out := []any{}
    if step > 0 {
        for i := start; i < stop; i += step {
            out = append(out, i)
        }
    } else {
        for i := start; i > stop; i += step {
            out = append(out, i)
        }
    }
    return out
}

func pyToFloat(v any) float64 {
    switch x := v.(type) {
    case int:
        return float64(x)
    case int64:
        return float64(x)
    case float64:
        return x
    case bool:
        if x {
            return 1.0
        }
        return 0.0
    default:
        panic("cannot convert to float")
    }
}

func pyToInt(v any) int {
    switch x := v.(type) {
    case int:
        return x
    case int64:
        return int(x)
    case float64:
        return int(math.Trunc(x))
    case bool:
        if x {
            return 1
        }
        return 0
    default:
        panic("cannot convert to int")
    }
}

func pyAdd(a, b any) any {
    if sa, ok := a.(string); ok {
        return sa + pyToString(b)
    }
    if sb, ok := b.(string); ok {
        return pyToString(a) + sb
    }
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) + pyToInt(b)
    }
    return pyToFloat(a) + pyToFloat(b)
}
func pySub(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) - pyToInt(b)
    }
    return pyToFloat(a) - pyToFloat(b)
}
func pyMul(a, b any) any {
    _, aInt := a.(int)
    _, bInt := b.(int)
    if aInt && bInt {
        return pyToInt(a) * pyToInt(b)
    }
    return pyToFloat(a) * pyToFloat(b)
}
func pyDiv(a, b any) any { return pyToFloat(a) / pyToFloat(b) }
func pyFloorDiv(a, b any) any { return int(math.Floor(pyToFloat(a) / pyToFloat(b))) }
func pyMod(a, b any) any {
    ai := pyToInt(a)
    bi := pyToInt(b)
    r := ai % bi
    if r != 0 && ((r > 0) != (bi > 0)) {
        r += bi
    }
    return r
}
func pyMin(values ...any) any {
    if len(values) == 0 {
        panic("min() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi < ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf < af {
            out = bf
        }
    }
    return out
}
func pyMax(values ...any) any {
    if len(values) == 0 {
        panic("max() arg is empty")
    }
    out := values[0]
    for i := 1; i < len(values); i++ {
        a := out
        b := values[i]
        if _, ok := a.(int); ok {
            if _, ok2 := b.(int); ok2 {
                ai := pyToInt(a)
                bi := pyToInt(b)
                if bi > ai {
                    out = bi
                }
                continue
            }
        }
        af := pyToFloat(a)
        bf := pyToFloat(b)
        if bf > af {
            out = bf
        }
    }
    return out
}
func pyLShift(a, b any) any { return pyToInt(a) << uint(pyToInt(b)) }
func pyRShift(a, b any) any { return pyToInt(a) >> uint(pyToInt(b)) }
func pyBitAnd(a, b any) any { return pyToInt(a) & pyToInt(b) }
func pyBitOr(a, b any) any  { return pyToInt(a) | pyToInt(b) }
func pyBitXor(a, b any) any { return pyToInt(a) ^ pyToInt(b) }
func pyNeg(a any) any {
    if _, ok := a.(int); ok {
        return -pyToInt(a)
    }
    return -pyToFloat(a)
}

func pyEq(a, b any) bool { return pyToString(a) == pyToString(b) }
func pyNe(a, b any) bool { return !pyEq(a, b) }
func pyLt(a, b any) bool { return pyToFloat(a) < pyToFloat(b) }
func pyLe(a, b any) bool { return pyToFloat(a) <= pyToFloat(b) }
func pyGt(a, b any) bool { return pyToFloat(a) > pyToFloat(b) }
func pyGe(a, b any) bool { return pyToFloat(a) >= pyToFloat(b) }

func pyIn(item, container any) bool {
    switch c := container.(type) {
    case string:
        return strings.Contains(c, pyToString(item))
    case []any:
        for _, v := range c {
            if pyEq(v, item) {
                return true
            }
        }
        return false
    case map[any]any:
        _, ok := c[item]
        return ok
    default:
        return false
    }
}

func pyIter(value any) []any {
    switch v := value.(type) {
    case []any:
        return v
    case []byte:
        out := make([]any, 0, len(v))
        for _, b := range v {
            out = append(out, int(b))
        }
        return out
    case string:
        out := []any{}
        for _, ch := range []rune(v) {
            out = append(out, string(ch))
        }
        return out
    case map[any]any:
        out := []any{}
        for k := range v {
            out = append(out, k)
        }
        return out
    default:
        panic("iter unsupported")
    }
}

func pyTernary(cond bool, a any, b any) any {
    if cond {
        return a
    }
    return b
}

func pyListFromIter(value any) any {
    it := pyIter(value)
    out := make([]any, len(it))
    copy(out, it)
    return out
}

func pySlice(value any, start any, end any) any {
    s := 0
    e := 0
    switch v := value.(type) {
    case string:
        r := []rune(v)
        n := len(r)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        return string(r[s:e])
    case []any:
        n := len(v)
        if start == nil {
            s = 0
        } else {
            s = pyToInt(start)
            if s < 0 {
                s += n
            }
            if s < 0 {
                s = 0
            }
            if s > n {
                s = n
            }
        }
        if end == nil {
            e = n
        } else {
            e = pyToInt(end)
            if e < 0 {
                e += n
            }
            if e < 0 {
                e = 0
            }
            if e > n {
                e = n
            }
        }
        if s > e {
            s = e
        }
        out := make([]any, e-s)
        copy(out, v[s:e])
        return out
    default:
        panic("slice unsupported")
    }
}

func pyGet(value any, key any) any {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return v[i]
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        return int(v[i])
    case map[any]any:
        return v[key]
    case string:
        r := []rune(v)
        i := pyToInt(key)
        if i < 0 {
            i += len(r)
        }
        return string(r[i])
    default:
        panic("subscript unsupported")
    }
}

func pySet(value any, key any, newValue any) {
    switch v := value.(type) {
    case []any:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = newValue
    case []byte:
        i := pyToInt(key)
        if i < 0 {
            i += len(v)
        }
        v[i] = byte(pyToInt(newValue))
    case map[any]any:
        v[key] = newValue
    default:
        panic("setitem unsupported")
    }
}

func pyPop(lst *any, idx any) any {
    arr := (*lst).([]any)
    n := len(arr)
    i := n - 1
    if idx != nil {
        i = pyToInt(idx)
        if i < 0 {
            i += n
        }
    }
    val := arr[i]
    arr = append(arr[:i], arr[i+1:]...)
    *lst = arr
    return val
}

func pyPopAt(container any, key any, idx any) any {
    lst := pyGet(container, key)
    val := pyPop(&lst, idx)
    pySet(container, key, lst)
    return val
}

func pyOrd(v any) any {
    s := pyToString(v)
    r := []rune(s)
    return int(r[0])
}

func pyChr(v any) any { return string(rune(pyToInt(v))) }

func pyBytearray(size any) any {
    if size == nil {
        return []byte{}
    }
    n := pyToInt(size)
    out := make([]byte, n)
    return out
}

func pyBytes(v any) any { return v }

func pyAppend(seq any, value any) any {
    switch s := seq.(type) {
    case []any:
        return append(s, value)
    case []byte:
        return append(s, byte(pyToInt(value)))
    default:
        panic("append unsupported type")
    }
}

func pyIsDigit(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if ch < '0' || ch > '9' {
            return false
        }
    }
    return true
}

func pyIsAlpha(v any) bool {
    s := pyToString(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z')) {
            return false
        }
    }
    return true
}

func pyTryCatch(body func() any, handler func(any) any, finalizer func()) (ret any) {
    defer finalizer()
    defer func() {
        if r := recover(); r != nil {
            ret = handler(r)
        }
    }()
    ret = body()
    return
}

// -------- time/math helper --------

func pyPerfCounter() any {
    return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func pyMathSqrt(v any) any { return math.Sqrt(pyToFloat(v)) }
func pyMathSin(v any) any  { return math.Sin(pyToFloat(v)) }
func pyMathCos(v any) any  { return math.Cos(pyToFloat(v)) }
func pyMathExp(v any) any  { return math.Exp(pyToFloat(v)) }
func pyMathFloor(v any) any { return float64(math.Floor(pyToFloat(v))) }
func pyMathPi() any        { return math.Pi }

// -------- png/gif helper --------

func pyToBytes(v any) []byte {
    switch x := v.(type) {
    case []byte:
        out := make([]byte, len(x))
        copy(out, x)
        return out
    case []any:
        out := make([]byte, len(x))
        for i, e := range x {
            out[i] = byte(pyToInt(e))
        }
        return out
    case string:
        return []byte(x)
    default:
        panic("cannot convert to bytes")
    }
}

func pyChunk(chunkType []byte, data []byte) []byte {
    var out bytes.Buffer
    n := uint32(len(data))
    out.Write([]byte{byte(n >> 24), byte(n >> 16), byte(n >> 8), byte(n)})
    out.Write(chunkType)
    out.Write(data)
    crc := crc32.ChecksumIEEE(append(append([]byte{}, chunkType...), data...))
    out.Write([]byte{byte(crc >> 24), byte(crc >> 16), byte(crc >> 8), byte(crc)})
    return out.Bytes()
}

func pyWriteRGBPNG(path any, width any, height any, pixels any) {
    w := pyToInt(width)
    h := pyToInt(height)
    raw := pyToBytes(pixels)
    expected := w * h * 3
    if len(raw) != expected {
        panic("pixels length mismatch")
    }

    scan := make([]byte, 0, h*(1+w*3))
    rowBytes := w * 3
    for y := 0; y < h; y++ {
        scan = append(scan, 0)
        start := y * rowBytes
        end := start + rowBytes
        scan = append(scan, raw[start:end]...)
    }

    var zbuf bytes.Buffer
    zw, _ := zlib.NewWriterLevel(&zbuf, 6)
    _, _ = zw.Write(scan)
    _ = zw.Close()
    idat := zbuf.Bytes()

    ihdr := []byte{
        byte(uint32(w) >> 24), byte(uint32(w) >> 16), byte(uint32(w) >> 8), byte(uint32(w)),
        byte(uint32(h) >> 24), byte(uint32(h) >> 16), byte(uint32(h) >> 8), byte(uint32(h)),
        8, 2, 0, 0, 0,
    }

    var png bytes.Buffer
    png.Write([]byte{0x89, 'P', 'N', 'G', '
', '
', 0x1a, '
'})
    png.Write(pyChunk([]byte("IHDR"), ihdr))
    png.Write(pyChunk([]byte("IDAT"), idat))
    png.Write(pyChunk([]byte("IEND"), []byte{}))

    _ = os.WriteFile(pyToString(path), png.Bytes(), 0o644)
}

func pyLzwEncode(data []byte, minCodeSize int) []byte {
    if len(data) == 0 {
        return []byte{}
    }
    clearCode := 1 << minCodeSize
    endCode := clearCode + 1
    codeSize := minCodeSize + 1
    out := []byte{}
    bitBuffer := 0
    bitCount := 0

    emit := func(code int) {
        bitBuffer |= (code << bitCount)
        bitCount += codeSize
        for bitCount >= 8 {
            out = append(out, byte(bitBuffer&0xff))
            bitBuffer >>= 8
            bitCount -= 8
        }
    }

    emit(clearCode)
    for _, v := range data {
        emit(int(v))
        emit(clearCode)
    }
    emit(endCode)
    if bitCount > 0 {
        out = append(out, byte(bitBuffer&0xff))
    }
    return out
}

func pyGrayscalePalette() any {
    p := make([]byte, 0, 256*3)
    for i := 0; i < 256; i++ {
        p = append(p, byte(i), byte(i), byte(i))
    }
    return p
}

func pySaveGIF(path any, width any, height any, frames any, palette any, delayCS any, loop any) {
    w := pyToInt(width)
    h := pyToInt(height)
    frameBytes := w * h
    pal := pyToBytes(palette)
    if len(pal) != 256*3 {
        panic("palette must be 256*3 bytes")
    }
    dcs := pyToInt(delayCS)
    lp := pyToInt(loop)

    frs := pyIter(frames)
    out := []byte{}
    out = append(out, []byte("GIF89a")...)
    out = append(out, byte(w), byte(w>>8), byte(h), byte(h>>8))
    out = append(out, 0xF7, 0, 0)
    out = append(out, pal...)

    out = append(out, 0x21, 0xFF, 0x0B)
    out = append(out, []byte("NETSCAPE2.0")...)
    out = append(out, 0x03, 0x01, byte(lp), byte(lp>>8), 0x00)

    for _, frAny := range frs {
        fr := pyToBytes(frAny)
        if len(fr) != frameBytes {
            panic("frame size mismatch")
        }
        out = append(out, 0x21, 0xF9, 0x04, 0x00, byte(dcs), byte(dcs>>8), 0x00, 0x00)
        out = append(out, 0x2C, 0, 0, 0, 0, byte(w), byte(w>>8), byte(h), byte(h>>8), 0x00)
        out = append(out, 0x08)
        compressed := pyLzwEncode(fr, 8)
        pos := 0
        for pos < len(compressed) {
            ln := len(compressed) - pos
            if ln > 255 {
                ln = 255
            }
            out = append(out, byte(ln))
            out = append(out, compressed[pos:pos+ln]...)
            pos += ln
        }
        out = append(out, 0x00)
    }
    out = append(out, 0x3B)
    _ = os.WriteFile(pyToString(path), out, 0o644)
}

func clamp01(v float64) any {
    if (pyBool((v < 0.0))) {
        return 0.0
    }
    if (pyBool((v > 1.0))) {
        return 1.0
    }
    return v
}

func dot(ax float64, ay float64, az float64, bx float64, by float64, bz float64) any {
    return (((ax * bx) + (ay * by)) + (az * bz))
}

func length(x float64, y float64, z float64) any {
    return math.Sqrt(pyToFloat((((x * x) + (y * y)) + (z * z))))
}

func normalize(x float64, y float64, z float64) any {
    var l any = length(x, y, z)
    _ = l
    if (pyBool(pyLt(l, 1e-09))) {
        return []any{0.0, 0.0, 0.0}
    }
    return []any{pyDiv(x, l), pyDiv(y, l), pyDiv(z, l)}
}

func reflect(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64) any {
    var d any = pyMul(dot(ix, iy, iz, nx, ny, nz), 2.0)
    _ = d
    return []any{pySub(ix, pyMul(d, nx)), pySub(iy, pyMul(d, ny)), pySub(iz, pyMul(d, nz))}
}

func refract(ix float64, iy float64, iz float64, nx float64, ny float64, nz float64, eta float64) any {
    var cosi any = pyNeg(dot(ix, iy, iz, nx, ny, nz))
    _ = cosi
    var sint2 any = pyMul((eta * eta), pySub(1.0, pyMul(cosi, cosi)))
    _ = sint2
    if (pyBool(pyGt(sint2, 1.0))) {
        return reflect(ix, iy, iz, nx, ny, nz)
    }
    var cost float64 = math.Sqrt(pyToFloat(pySub(1.0, sint2)))
    _ = cost
    var k any = pySub(pyMul(eta, cosi), cost)
    _ = k
    return []any{pyAdd((eta * ix), pyMul(k, nx)), pyAdd((eta * iy), pyMul(k, ny)), pyAdd((eta * iz), pyMul(k, nz))}
}

func schlick(cos_theta float64, f0 float64) any {
    var m float64 = (1.0 - cos_theta)
    _ = m
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))
}

func sky_color(dx float64, dy float64, dz float64, tphase float64) any {
    var t float64 = (0.5 * (dy + 1.0))
    _ = t
    var r float64 = (0.06 + (0.2 * t))
    _ = r
    var g float64 = (0.1 + (0.25 * t))
    _ = g
    var b float64 = (0.16 + (0.45 * t))
    _ = b
    var band float64 = (0.5 + (0.5 * math.Sin(pyToFloat((((8.0 * dx) + (6.0 * dz)) + tphase)))))
    _ = band
    r = (r + (0.08 * band))
    g = (g + (0.05 * band))
    b = (b + (0.12 * band))
    return []any{clamp01(r), clamp01(g), clamp01(b)}
}

func sphere_intersect(ox float64, oy float64, oz float64, dx float64, dy float64, dz float64, cx float64, cy float64, cz float64, radius float64) any {
    var lx float64 = (ox - cx)
    _ = lx
    var ly float64 = (oy - cy)
    _ = ly
    var lz float64 = (oz - cz)
    _ = lz
    var b float64 = (((lx * dx) + (ly * dy)) + (lz * dz))
    _ = b
    var c float64 = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
    _ = c
    var h float64 = ((b * b) - c)
    _ = h
    if (pyBool((h < 0.0))) {
        return (-1.0)
    }
    var s float64 = math.Sqrt(pyToFloat(h))
    _ = s
    var t0 float64 = ((-b) - s)
    _ = t0
    if (pyBool((t0 > 0.0001))) {
        return t0
    }
    var t1 float64 = ((-b) + s)
    _ = t1
    if (pyBool((t1 > 0.0001))) {
        return t1
    }
    return (-1.0)
}

func palette_332() any {
    var p any = pyBytearray((256 * 3))
    _ = p
    __pytra_range_start_1 := pyToInt(0)
    __pytra_range_stop_2 := pyToInt(256)
    __pytra_range_step_3 := pyToInt(1)
    if __pytra_range_step_3 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_4 := __pytra_range_start_1; (__pytra_range_step_3 > 0 && __pytra_i_4 < __pytra_range_stop_2) || (__pytra_range_step_3 < 0 && __pytra_i_4 > __pytra_range_stop_2); __pytra_i_4 += __pytra_range_step_3 {
        i = __pytra_i_4
        var r int = ((i >> uint(5)) & 7)
        _ = r
        var g int = ((i >> uint(2)) & 7)
        _ = g
        var b int = (i & 3)
        _ = b
        pySet(p, ((i * 3) + 0), pyToInt((float64((255 * r)) / float64(7))))
        pySet(p, ((i * 3) + 1), pyToInt((float64((255 * g)) / float64(7))))
        pySet(p, ((i * 3) + 2), pyToInt((float64((255 * b)) / float64(3))))
    }
    return pyBytes(p)
}

func quantize_332(r float64, g float64, b float64) any {
    var rr int = pyToInt(pyMul(clamp01(r), 255.0))
    _ = rr
    var gg int = pyToInt(pyMul(clamp01(g), 255.0))
    _ = gg
    var bb int = pyToInt(pyMul(clamp01(b), 255.0))
    _ = bb
    return ((((rr >> uint(5)) << uint(5)) + ((gg >> uint(5)) << uint(2))) + (bb >> uint(6)))
}

func render_frame(width int, height int, frame_id int, frames_n int) any {
    var t float64 = (float64(frame_id) / float64(frames_n))
    _ = t
    var tphase any = pyMul(pyMul(2.0, pyMathPi()), t)
    _ = tphase
    var cam_r float64 = 3.0
    _ = cam_r
    var cam_x float64 = (cam_r * math.Cos(pyToFloat(pyMul(tphase, 0.9))))
    _ = cam_x
    var cam_y float64 = (1.1 + (0.25 * math.Sin(pyToFloat(pyMul(tphase, 0.6)))))
    _ = cam_y
    var cam_z float64 = (cam_r * math.Sin(pyToFloat(pyMul(tphase, 0.9))))
    _ = cam_z
    var look_x float64 = 0.0
    _ = look_x
    var look_y float64 = 0.35
    _ = look_y
    var look_z float64 = 0.0
    _ = look_z
    var __pytra_tuple_5 any = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z))
    _ = __pytra_tuple_5
    var fwd_x any = pyGet(__pytra_tuple_5, 0)
    _ = fwd_x
    var fwd_y any = pyGet(__pytra_tuple_5, 1)
    _ = fwd_y
    var fwd_z any = pyGet(__pytra_tuple_5, 2)
    _ = fwd_z
    var __pytra_tuple_6 any = normalize(pyToFloat(fwd_z), 0.0, pyToFloat(pyNeg(fwd_x)))
    _ = __pytra_tuple_6
    var right_x any = pyGet(__pytra_tuple_6, 0)
    _ = right_x
    var right_y any = pyGet(__pytra_tuple_6, 1)
    _ = right_y
    var right_z any = pyGet(__pytra_tuple_6, 2)
    _ = right_z
    var __pytra_tuple_7 any = normalize(pyToFloat(pySub(pyMul(right_y, fwd_z), pyMul(right_z, fwd_y))), pyToFloat(pySub(pyMul(right_z, fwd_x), pyMul(right_x, fwd_z))), pyToFloat(pySub(pyMul(right_x, fwd_y), pyMul(right_y, fwd_x))))
    _ = __pytra_tuple_7
    var up_x any = pyGet(__pytra_tuple_7, 0)
    _ = up_x
    var up_y any = pyGet(__pytra_tuple_7, 1)
    _ = up_y
    var up_z any = pyGet(__pytra_tuple_7, 2)
    _ = up_z
    var s0x float64 = (0.9 * math.Cos(pyToFloat(pyMul(1.3, tphase))))
    _ = s0x
    var s0y float64 = (0.15 + (0.35 * math.Sin(pyToFloat(pyMul(1.7, tphase)))))
    _ = s0y
    var s0z float64 = (0.9 * math.Sin(pyToFloat(pyMul(1.3, tphase))))
    _ = s0z
    var s1x float64 = (1.2 * math.Cos(pyToFloat(pyAdd(pyMul(1.3, tphase), 2.094))))
    _ = s1x
    var s1y float64 = (0.1 + (0.4 * math.Sin(pyToFloat(pyAdd(pyMul(1.1, tphase), 0.8)))))
    _ = s1y
    var s1z float64 = (1.2 * math.Sin(pyToFloat(pyAdd(pyMul(1.3, tphase), 2.094))))
    _ = s1z
    var s2x float64 = (1.0 * math.Cos(pyToFloat(pyAdd(pyMul(1.3, tphase), 4.188))))
    _ = s2x
    var s2y float64 = (0.2 + (0.3 * math.Sin(pyToFloat(pyAdd(pyMul(1.5, tphase), 1.9)))))
    _ = s2y
    var s2z float64 = (1.0 * math.Sin(pyToFloat(pyAdd(pyMul(1.3, tphase), 4.188))))
    _ = s2z
    var lr float64 = 0.35
    _ = lr
    var lx float64 = (2.4 * math.Cos(pyToFloat(pyMul(tphase, 1.8))))
    _ = lx
    var ly float64 = (1.8 + (0.8 * math.Sin(pyToFloat(pyMul(tphase, 1.2)))))
    _ = ly
    var lz float64 = (2.4 * math.Sin(pyToFloat(pyMul(tphase, 1.8))))
    _ = lz
    var frame any = pyBytearray((width * height))
    _ = frame
    var aspect float64 = (float64(width) / float64(height))
    _ = aspect
    var fov float64 = 1.25
    _ = fov
    var i int = 0
    _ = i
    __pytra_range_start_8 := pyToInt(0)
    __pytra_range_stop_9 := pyToInt(height)
    __pytra_range_step_10 := pyToInt(1)
    if __pytra_range_step_10 == 0 { panic("range() step must not be zero") }
    var py int = 0
    _ = py
    for __pytra_i_11 := __pytra_range_start_8; (__pytra_range_step_10 > 0 && __pytra_i_11 < __pytra_range_stop_9) || (__pytra_range_step_10 < 0 && __pytra_i_11 > __pytra_range_stop_9); __pytra_i_11 += __pytra_range_step_10 {
        py = __pytra_i_11
        var sy float64 = (1.0 - ((2.0 * (float64(py) + 0.5)) / float64(height)))
        _ = sy
        __pytra_range_start_12 := pyToInt(0)
        __pytra_range_stop_13 := pyToInt(width)
        __pytra_range_step_14 := pyToInt(1)
        if __pytra_range_step_14 == 0 { panic("range() step must not be zero") }
        var px int = 0
        _ = px
        for __pytra_i_15 := __pytra_range_start_12; (__pytra_range_step_14 > 0 && __pytra_i_15 < __pytra_range_stop_13) || (__pytra_range_step_14 < 0 && __pytra_i_15 > __pytra_range_stop_13); __pytra_i_15 += __pytra_range_step_14 {
            px = __pytra_i_15
            var sx float64 = ((((2.0 * (float64(px) + 0.5)) / float64(width)) - 1.0) * aspect)
            _ = sx
            var rx any = pyAdd(fwd_x, pyMul(fov, pyAdd(pyMul(sx, right_x), pyMul(sy, up_x))))
            _ = rx
            var ry any = pyAdd(fwd_y, pyMul(fov, pyAdd(pyMul(sx, right_y), pyMul(sy, up_y))))
            _ = ry
            var rz any = pyAdd(fwd_z, pyMul(fov, pyAdd(pyMul(sx, right_z), pyMul(sy, up_z))))
            _ = rz
            var __pytra_tuple_16 any = normalize(pyToFloat(rx), pyToFloat(ry), pyToFloat(rz))
            _ = __pytra_tuple_16
            var dx any = pyGet(__pytra_tuple_16, 0)
            _ = dx
            var dy any = pyGet(__pytra_tuple_16, 1)
            _ = dy
            var dz any = pyGet(__pytra_tuple_16, 2)
            _ = dz
            var best_t float64 = 1000000000.0
            _ = best_t
            var hit_kind int = 0
            _ = hit_kind
            var r float64 = 0.0
            _ = r
            var g float64 = 0.0
            _ = g
            var b float64 = 0.0
            _ = b
            if (pyBool(pyLt(dy, (-1e-06)))) {
                var tf any = pyDiv(((-1.2) - cam_y), dy)
                _ = tf
                if (pyBool((pyBool(pyGt(tf, 0.0001)) && pyBool(pyLt(tf, best_t))))) {
                    best_t = pyToFloat(tf)
                    hit_kind = 1
                }
            }
            var t0 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s0x, s0y, s0z, 0.65)
            _ = t0
            if (pyBool((pyBool(pyGt(t0, 0.0)) && pyBool(pyLt(t0, best_t))))) {
                best_t = pyToFloat(t0)
                hit_kind = 2
            }
            var t1 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s1x, s1y, s1z, 0.72)
            _ = t1
            if (pyBool((pyBool(pyGt(t1, 0.0)) && pyBool(pyLt(t1, best_t))))) {
                best_t = pyToFloat(t1)
                hit_kind = 3
            }
            var t2 any = sphere_intersect(cam_x, cam_y, cam_z, pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), s2x, s2y, s2z, 0.58)
            _ = t2
            if (pyBool((pyBool(pyGt(t2, 0.0)) && pyBool(pyLt(t2, best_t))))) {
                best_t = pyToFloat(t2)
                hit_kind = 4
            }
            if (pyBool((hit_kind == 0))) {
                var __pytra_tuple_17 any = sky_color(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(tphase))
                _ = __pytra_tuple_17
                r = pyToFloat(pyGet(__pytra_tuple_17, 0))
                g = pyToFloat(pyGet(__pytra_tuple_17, 1))
                b = pyToFloat(pyGet(__pytra_tuple_17, 2))
            } else {
                if (pyBool((hit_kind == 1))) {
                    var hx any = pyAdd(cam_x, pyMul(best_t, dx))
                    _ = hx
                    var hz any = pyAdd(cam_z, pyMul(best_t, dz))
                    _ = hz
                    var cx int = pyToInt(math.Floor(pyToFloat(pyMul(hx, 2.0))))
                    _ = cx
                    var cz int = pyToInt(math.Floor(pyToFloat(pyMul(hz, 2.0))))
                    _ = cz
                    var checker any = pyTernary(pyBool((((cx + cz) % 2) == 0)), 0, 1)
                    _ = checker
                    var base_r any = pyTernary(pyBool(pyEq(checker, 0)), 0.1, 0.04)
                    _ = base_r
                    var base_g any = pyTernary(pyBool(pyEq(checker, 0)), 0.11, 0.05)
                    _ = base_g
                    var base_b any = pyTernary(pyBool(pyEq(checker, 0)), 0.13, 0.08)
                    _ = base_b
                    var lxv any = pySub(lx, hx)
                    _ = lxv
                    var lyv float64 = (ly - (-1.2))
                    _ = lyv
                    var lzv any = pySub(lz, hz)
                    _ = lzv
                    var __pytra_tuple_18 any = normalize(pyToFloat(lxv), lyv, pyToFloat(lzv))
                    _ = __pytra_tuple_18
                    var ldx any = pyGet(__pytra_tuple_18, 0)
                    _ = ldx
                    var ldy any = pyGet(__pytra_tuple_18, 1)
                    _ = ldy
                    var ldz any = pyGet(__pytra_tuple_18, 2)
                    _ = ldz
                    var ndotl any = pyMax(ldy, 0.0)
                    _ = ndotl
                    var ldist2 any = pyAdd(pyAdd(pyMul(lxv, lxv), (lyv * lyv)), pyMul(lzv, lzv))
                    _ = ldist2
                    var glow any = pyDiv(8.0, pyAdd(1.0, ldist2))
                    _ = glow
                    r = pyToFloat(pyAdd(pyAdd(base_r, pyMul(0.8, glow)), pyMul(0.2, ndotl)))
                    g = pyToFloat(pyAdd(pyAdd(base_g, pyMul(0.5, glow)), pyMul(0.18, ndotl)))
                    b = pyToFloat(pyAdd(pyAdd(base_b, pyMul(1.0, glow)), pyMul(0.24, ndotl)))
                } else {
                    var cx float64 = 0.0
                    _ = cx
                    var cy float64 = 0.0
                    _ = cy
                    var cz float64 = 0.0
                    _ = cz
                    var rad float64 = 1.0
                    _ = rad
                    if (pyBool((hit_kind == 2))) {
                        cx = s0x
                        cy = s0y
                        cz = s0z
                        rad = 0.65
                    } else {
                        if (pyBool((hit_kind == 3))) {
                            cx = s1x
                            cy = s1y
                            cz = s1z
                            rad = 0.72
                        } else {
                            cx = s2x
                            cy = s2y
                            cz = s2z
                            rad = 0.58
                        }
                    }
                    var hx any = pyAdd(cam_x, pyMul(best_t, dx))
                    _ = hx
                    var hy any = pyAdd(cam_y, pyMul(best_t, dy))
                    _ = hy
                    var hz any = pyAdd(cam_z, pyMul(best_t, dz))
                    _ = hz
                    var __pytra_tuple_19 any = normalize(pyToFloat(pyDiv(pySub(hx, cx), rad)), pyToFloat(pyDiv(pySub(hy, cy), rad)), pyToFloat(pyDiv(pySub(hz, cz), rad)))
                    _ = __pytra_tuple_19
                    var nx any = pyGet(__pytra_tuple_19, 0)
                    _ = nx
                    var ny any = pyGet(__pytra_tuple_19, 1)
                    _ = ny
                    var nz any = pyGet(__pytra_tuple_19, 2)
                    _ = nz
                    var __pytra_tuple_20 any = reflect(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(nx), pyToFloat(ny), pyToFloat(nz))
                    _ = __pytra_tuple_20
                    var rdx any = pyGet(__pytra_tuple_20, 0)
                    _ = rdx
                    var rdy any = pyGet(__pytra_tuple_20, 1)
                    _ = rdy
                    var rdz any = pyGet(__pytra_tuple_20, 2)
                    _ = rdz
                    var __pytra_tuple_21 any = refract(pyToFloat(dx), pyToFloat(dy), pyToFloat(dz), pyToFloat(nx), pyToFloat(ny), pyToFloat(nz), (1.0 / 1.45))
                    _ = __pytra_tuple_21
                    var tdx any = pyGet(__pytra_tuple_21, 0)
                    _ = tdx
                    var tdy any = pyGet(__pytra_tuple_21, 1)
                    _ = tdy
                    var tdz any = pyGet(__pytra_tuple_21, 2)
                    _ = tdz
                    var __pytra_tuple_22 any = sky_color(pyToFloat(rdx), pyToFloat(rdy), pyToFloat(rdz), pyToFloat(tphase))
                    _ = __pytra_tuple_22
                    var sr any = pyGet(__pytra_tuple_22, 0)
                    _ = sr
                    var sg any = pyGet(__pytra_tuple_22, 1)
                    _ = sg
                    var sb any = pyGet(__pytra_tuple_22, 2)
                    _ = sb
                    var __pytra_tuple_23 any = sky_color(pyToFloat(tdx), pyToFloat(tdy), pyToFloat(tdz), pyToFloat(pyAdd(tphase, 0.8)))
                    _ = __pytra_tuple_23
                    var tr any = pyGet(__pytra_tuple_23, 0)
                    _ = tr
                    var tg any = pyGet(__pytra_tuple_23, 1)
                    _ = tg
                    var tb any = pyGet(__pytra_tuple_23, 2)
                    _ = tb
                    var cosi any = pyMax(pyNeg(pyAdd(pyAdd(pyMul(dx, nx), pyMul(dy, ny)), pyMul(dz, nz))), 0.0)
                    _ = cosi
                    var fr any = schlick(pyToFloat(cosi), 0.04)
                    _ = fr
                    r = pyToFloat(pyAdd(pyMul(tr, pySub(1.0, fr)), pyMul(sr, fr)))
                    g = pyToFloat(pyAdd(pyMul(tg, pySub(1.0, fr)), pyMul(sg, fr)))
                    b = pyToFloat(pyAdd(pyMul(tb, pySub(1.0, fr)), pyMul(sb, fr)))
                    var lxv any = pySub(lx, hx)
                    _ = lxv
                    var lyv any = pySub(ly, hy)
                    _ = lyv
                    var lzv any = pySub(lz, hz)
                    _ = lzv
                    var __pytra_tuple_24 any = normalize(pyToFloat(lxv), pyToFloat(lyv), pyToFloat(lzv))
                    _ = __pytra_tuple_24
                    var ldx any = pyGet(__pytra_tuple_24, 0)
                    _ = ldx
                    var ldy any = pyGet(__pytra_tuple_24, 1)
                    _ = ldy
                    var ldz any = pyGet(__pytra_tuple_24, 2)
                    _ = ldz
                    var ndotl any = pyMax(pyAdd(pyAdd(pyMul(nx, ldx), pyMul(ny, ldy)), pyMul(nz, ldz)), 0.0)
                    _ = ndotl
                    var __pytra_tuple_25 any = normalize(pyToFloat(pySub(ldx, dx)), pyToFloat(pySub(ldy, dy)), pyToFloat(pySub(ldz, dz)))
                    _ = __pytra_tuple_25
                    var hvx any = pyGet(__pytra_tuple_25, 0)
                    _ = hvx
                    var hvy any = pyGet(__pytra_tuple_25, 1)
                    _ = hvy
                    var hvz any = pyGet(__pytra_tuple_25, 2)
                    _ = hvz
                    var ndoth any = pyMax(pyAdd(pyAdd(pyMul(nx, hvx), pyMul(ny, hvy)), pyMul(nz, hvz)), 0.0)
                    _ = ndoth
                    var spec any = pyMul(ndoth, ndoth)
                    _ = spec
                    spec = pyMul(spec, spec)
                    spec = pyMul(spec, spec)
                    spec = pyMul(spec, spec)
                    var glow any = pyDiv(10.0, pyAdd(pyAdd(pyAdd(1.0, pyMul(lxv, lxv)), pyMul(lyv, lyv)), pyMul(lzv, lzv)))
                    _ = glow
                    r = (r + pyToFloat(pyAdd(pyAdd(pyMul(0.2, ndotl), pyMul(0.8, spec)), pyMul(0.45, glow))))
                    g = (g + pyToFloat(pyAdd(pyAdd(pyMul(0.18, ndotl), pyMul(0.6, spec)), pyMul(0.35, glow))))
                    b = (b + pyToFloat(pyAdd(pyAdd(pyMul(0.26, ndotl), pyMul(1.0, spec)), pyMul(0.65, glow))))
                    if (pyBool((hit_kind == 2))) {
                        r = (r * 0.95)
                        g = (g * 1.05)
                        b = (b * 1.1)
                    } else {
                        if (pyBool((hit_kind == 3))) {
                            r = (r * 1.08)
                            g = (g * 0.98)
                            b = (b * 1.04)
                        } else {
                            r = (r * 1.02)
                            g = (g * 1.1)
                            b = (b * 0.95)
                        }
                    }
                }
            }
            r = math.Sqrt(pyToFloat(clamp01(r)))
            g = math.Sqrt(pyToFloat(clamp01(g)))
            b = math.Sqrt(pyToFloat(clamp01(b)))
            pySet(frame, i, quantize_332(r, g, b))
            i = (i + 1)
        }
    }
    return pyBytes(frame)
}

func run_16_glass_sculpture_chaos() any {
    var width int = 320
    _ = width
    var height int = 240
    _ = height
    var frames_n int = 72
    _ = frames_n
    var out_path string = "sample/out/16_glass_sculpture_chaos.gif"
    _ = out_path
    var start any = pyPerfCounter()
    _ = start
    var frames any = []any{}
    _ = frames
    __pytra_range_start_26 := pyToInt(0)
    __pytra_range_stop_27 := pyToInt(frames_n)
    __pytra_range_step_28 := pyToInt(1)
    if __pytra_range_step_28 == 0 { panic("range() step must not be zero") }
    var i int = 0
    _ = i
    for __pytra_i_29 := __pytra_range_start_26; (__pytra_range_step_28 > 0 && __pytra_i_29 < __pytra_range_stop_27) || (__pytra_range_step_28 < 0 && __pytra_i_29 > __pytra_range_stop_27); __pytra_i_29 += __pytra_range_step_28 {
        i = __pytra_i_29
        frames = pyAppend(frames, render_frame(width, height, i, frames_n))
    }
    pySaveGIF(out_path, width, height, frames, palette_332(), 6, 0)
    var elapsed any = pySub(pyPerfCounter(), start)
    _ = elapsed
    pyPrint("output:", out_path)
    pyPrint("frames:", frames_n)
    pyPrint("elapsed_sec:", elapsed)
    return nil
}

func main() {
    run_16_glass_sculpture_chaos()
}
```
</details>

<details>
<summary>Javaへの変換例 : 16_glass_sculpture_chaos.java</summary>

```java
// このファイルは自動生成です（Python -> Java native mode）。

// Java ネイティブ変換向け Python 互換ランタイム補助。

import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringJoiner;
import java.util.zip.CRC32;
import java.util.zip.Deflater;

final class PyRuntime {
    private PyRuntime() {
    }

    static String pyToString(Object v) {
        if (v == null) {
            return "None";
        }
        if (v instanceof Boolean b) {
            return b ? "True" : "False";
        }
        if (v instanceof List<?> list) {
            StringJoiner sj = new StringJoiner(", ", "[", "]");
            for (Object it : list) {
                sj.add(pyToString(it));
            }
            return sj.toString();
        }
        if (v instanceof Map<?, ?> map) {
            StringJoiner sj = new StringJoiner(", ", "{", "}");
            for (Map.Entry<?, ?> e : map.entrySet()) {
                sj.add(pyToString(e.getKey()) + ": " + pyToString(e.getValue()));
            }
            return sj.toString();
        }
        return String.valueOf(v);
    }

    static void pyPrint(Object... values) {
        StringJoiner sj = new StringJoiner(" ");
        for (Object value : values) {
            sj.add(pyToString(value));
        }
        System.out.println(sj);
    }

    static boolean pyBool(Object v) {
        if (v == null) {
            return false;
        }
        if (v instanceof Boolean b) {
            return b;
        }
        if (v instanceof Integer i) {
            return i != 0;
        }
        if (v instanceof Long i) {
            return i != 0L;
        }
        if (v instanceof Double d) {
            return d != 0.0;
        }
        if (v instanceof String s) {
            return !s.isEmpty();
        }
        if (v instanceof List<?> list) {
            return !list.isEmpty();
        }
        if (v instanceof Map<?, ?> map) {
            return !map.isEmpty();
        }
        return true;
    }

    static int pyLen(Object v) {
        if (v instanceof String s) {
            return s.length();
        }
        if (v instanceof List<?> list) {
            return list.size();
        }
        if (v instanceof byte[] bytes) {
            return bytes.length;
        }
        if (v instanceof Map<?, ?> map) {
            return map.size();
        }
        throw new RuntimeException("len() unsupported type");
    }

    static List<Object> pyRange(int start, int stop, int step) {
        if (step == 0) {
            throw new RuntimeException("range() step must not be zero");
        }
        List<Object> out = new ArrayList<>();
        if (step > 0) {
            for (int i = start; i < stop; i += step) {
                out.add(i);
            }
        } else {
            for (int i = start; i > stop; i += step) {
                out.add(i);
            }
        }
        return out;
    }

    static double pyToFloat(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return i;
        }
        if (v instanceof Double d) {
            return d;
        }
        if (v instanceof Boolean b) {
            return b ? 1.0 : 0.0;
        }
        throw new RuntimeException("cannot convert to float");
    }

    static int pyToInt(Object v) {
        if (v instanceof Integer i) {
            return i;
        }
        if (v instanceof Long i) {
            return (int) i.longValue();
        }
        if (v instanceof Double d) {
            // Python の int() は小数部切り捨て（0方向）なので Java のキャストで合わせる。
            return (int) d.doubleValue();
        }
        if (v instanceof Boolean b) {
            return b ? 1 : 0;
        }
        throw new RuntimeException("cannot convert to int");
    }

    static long pyToLong(Object v) {
        if (v instanceof Integer i) {
            return i.longValue();
        }
        if (v instanceof Long i) {
            return i.longValue();
        }
        if (v instanceof Double d) {
            return (long) d.doubleValue();
        }
        if (v instanceof Boolean b) {
            return b ? 1L : 0L;
        }
        throw new RuntimeException("cannot convert to long");
    }

    static Object pyAdd(Object a, Object b) {
        if (a instanceof String || b instanceof String) {
            return pyToString(a) + pyToString(b);
        }
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) + pyToLong(b);
        }
        return pyToFloat(a) + pyToFloat(b);
    }

    static Object pySub(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) - pyToLong(b);
        }
        return pyToFloat(a) - pyToFloat(b);
    }

    static Object pyMul(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            return pyToLong(a) * pyToLong(b);
        }
        return pyToFloat(a) * pyToFloat(b);
    }

    static Object pyDiv(Object a, Object b) {
        return pyToFloat(a) / pyToFloat(b);
    }

    static Object pyFloorDiv(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long q = ai / bi;
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                q -= 1;
            }
            return q;
        }
        return (int) Math.floor(pyToFloat(a) / pyToFloat(b));
    }

    static Object pyMod(Object a, Object b) {
        if ((a instanceof Integer || a instanceof Long || a instanceof Boolean)
                && (b instanceof Integer || b instanceof Long || b instanceof Boolean)) {
            long ai = pyToLong(a);
            long bi = pyToLong(b);
            long r = ai % bi;
            if (r != 0 && ((r > 0) != (bi > 0))) {
                r += bi;
            }
            return r;
        }
        throw new RuntimeException("mod unsupported type");
    }

    static Object pyMin(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("min() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) < pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) < pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) < pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object pyMax(Object... values) {
        if (values.length == 0) {
            throw new RuntimeException("max() arg is empty");
        }
        Object out = values[0];
        for (int i = 1; i < values.length; i++) {
            Object a = out;
            Object b = values[i];
            if (a instanceof Long || b instanceof Long) {
                if (pyToLong(b) > pyToLong(a)) {
                    out = b;
                }
                continue;
            }
            if (a instanceof Integer && b instanceof Integer) {
                if (pyToInt(b) > pyToInt(a)) {
                    out = b;
                }
            } else if (pyToFloat(b) > pyToFloat(a)) {
                out = b;
            }
        }
        return out;
    }

    static Object pyLShift(Object a, Object b) {
        return pyToInt(a) << pyToInt(b);
    }

    static Object pyRShift(Object a, Object b) {
        return pyToInt(a) >> pyToInt(b);
    }

    static Object pyBitAnd(Object a, Object b) {
        return pyToInt(a) & pyToInt(b);
    }

    static Object pyBitOr(Object a, Object b) {
        return pyToInt(a) | pyToInt(b);
    }

    static Object pyBitXor(Object a, Object b) {
        return pyToInt(a) ^ pyToInt(b);
    }

    static Object pyNeg(Object a) {
        if (a instanceof Integer || a instanceof Long || a instanceof Boolean) {
            return -pyToLong(a);
        }
        return -pyToFloat(a);
    }

    static boolean pyEq(Object a, Object b) {
        return pyToString(a).equals(pyToString(b));
    }

    static boolean pyNe(Object a, Object b) {
        return !pyEq(a, b);
    }

    static boolean pyLt(Object a, Object b) {
        return pyToFloat(a) < pyToFloat(b);
    }

    static boolean pyLe(Object a, Object b) {
        return pyToFloat(a) <= pyToFloat(b);
    }

    static boolean pyGt(Object a, Object b) {
        return pyToFloat(a) > pyToFloat(b);
    }

    static boolean pyGe(Object a, Object b) {
        return pyToFloat(a) >= pyToFloat(b);
    }

    static boolean pyIn(Object item, Object container) {
        if (container instanceof String s) {
            return s.contains(pyToString(item));
        }
        if (container instanceof List<?> list) {
            for (Object v : list) {
                if (pyEq(v, item)) {
                    return true;
                }
            }
            return false;
        }
        if (container instanceof Map<?, ?> map) {
            return map.containsKey(item);
        }
        return false;
    }

    static List<Object> pyIter(Object value) {
        if (value instanceof List<?> list) {
            return new ArrayList<>((List<Object>) list);
        }
        if (value instanceof byte[] arr) {
            List<Object> out = new ArrayList<>();
            for (byte b : arr) {
                out.add((int) (b & 0xff));
            }
            return out;
        }
        if (value instanceof String s) {
            List<Object> out = new ArrayList<>();
            for (int i = 0; i < s.length(); i++) {
                out.add(String.valueOf(s.charAt(i)));
            }
            return out;
        }
        if (value instanceof Map<?, ?> map) {
            return new ArrayList<>(((Map<Object, Object>) map).keySet());
        }
        throw new RuntimeException("iter unsupported");
    }

    static Object pyTernary(boolean cond, Object a, Object b) {
        return cond ? a : b;
    }

    static Object pyListFromIter(Object value) {
        return pyIter(value);
    }

    static Object pySlice(Object value, Object start, Object end) {
        if (value instanceof String s) {
            int n = s.length();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return s.substring(st, ed);
        }
        if (value instanceof List<?> list) {
            int n = list.size();
            int st = (start == null) ? 0 : pyToInt(start);
            int ed = (end == null) ? n : pyToInt(end);
            if (st < 0)
                st += n;
            if (ed < 0)
                ed += n;
            if (st < 0)
                st = 0;
            if (ed < 0)
                ed = 0;
            if (st > n)
                st = n;
            if (ed > n)
                ed = n;
            if (st > ed)
                st = ed;
            return new ArrayList<>(list.subList(st, ed));
        }
        throw new RuntimeException("slice unsupported");
    }

    static Object pyGet(Object value, Object key) {
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            if (i < 0)
                i += list.size();
            return list.get(i);
        }
        if (value instanceof Map<?, ?> map) {
            return ((Map<Object, Object>) map).get(key);
        }
        if (value instanceof String s) {
            int i = pyToInt(key);
            if (i < 0)
                i += s.length();
            return String.valueOf(s.charAt(i));
        }
        throw new RuntimeException("subscript unsupported");
    }

    static void pySet(Object value, Object key, Object newValue) {
        if (value instanceof List<?> list) {
            int i = pyToInt(key);
            List<Object> l = (List<Object>) list;
            if (i < 0)
                i += l.size();
            l.set(i, newValue);
            return;
        }
        if (value instanceof Map<?, ?> map) {
            ((Map<Object, Object>) map).put(key, newValue);
            return;
        }
        throw new RuntimeException("setitem unsupported");
    }

    static Object pyPop(Object value, Object idx) {
        if (value instanceof List<?> list) {
            List<Object> l = (List<Object>) list;
            int i = (idx == null) ? (l.size() - 1) : pyToInt(idx);
            if (i < 0)
                i += l.size();
            Object out = l.get(i);
            l.remove(i);
            return out;
        }
        throw new RuntimeException("pop unsupported");
    }

    static Object pyOrd(Object v) {
        String s = pyToString(v);
        return (int) s.charAt(0);
    }

    static Object pyChr(Object v) {
        return Character.toString((char) pyToInt(v));
    }

    static Object pyBytearray(Object size) {
        int n = (size == null) ? 0 : pyToInt(size);
        List<Object> out = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            out.add(0);
        }
        return out;
    }

    static Object pyBytes(Object v) {
        return v;
    }

    static boolean pyIsDigit(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < '0' || c > '9') {
                return false;
            }
        }
        return true;
    }

    static boolean pyIsAlpha(Object v) {
        String s = pyToString(v);
        if (s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z'))) {
                return false;
            }
        }
        return true;
    }

    static List<Object> pyList(Object... items) {
        List<Object> out = new ArrayList<>();
        for (Object item : items) {
            out.add(item);
        }
        return out;
    }

    static Map<Object, Object> pyDict(Object... kv) {
        Map<Object, Object> out = new HashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            out.put(kv[i], kv[i + 1]);
        }
        return out;
    }

    // --- time/math ---

    static Object pyPerfCounter() {
        return System.nanoTime() / 1_000_000_000.0;
    }

    static Object pyMathSqrt(Object v) {
        return Math.sqrt(pyToFloat(v));
    }

    static Object pyMathSin(Object v) {
        return Math.sin(pyToFloat(v));
    }

    static Object pyMathCos(Object v) {
        return Math.cos(pyToFloat(v));
    }

    static Object pyMathExp(Object v) {
        return Math.exp(pyToFloat(v));
    }

    static Object pyMathFloor(Object v) {
        return Math.floor(pyToFloat(v));
    }

    static Object pyMathPi() {
        return Math.PI;
    }

    // --- png/gif ---

    static byte[] pyToBytes(Object v) {
        if (v instanceof byte[] b) {
            return b;
        }
        if (v instanceof List<?> list) {
            byte[] out = new byte[list.size()];
            for (int i = 0; i < list.size(); i++) {
                out[i] = (byte) pyToInt(list.get(i));
            }
            return out;
        }
        if (v instanceof String s) {
            return s.getBytes(StandardCharsets.UTF_8);
        }
        throw new RuntimeException("cannot convert to bytes");
    }

    static byte[] pyChunk(String chunkType, byte[] data) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            int n = data.length;
            out.write((n >>> 24) & 0xff);
            out.write((n >>> 16) & 0xff);
            out.write((n >>> 8) & 0xff);
            out.write(n & 0xff);
            byte[] typeBytes = chunkType.getBytes(StandardCharsets.US_ASCII);
            out.write(typeBytes);
            out.write(data);
            CRC32 crc = new CRC32();
            crc.update(typeBytes);
            crc.update(data);
            long c = crc.getValue();
            out.write((int) ((c >>> 24) & 0xff));
            out.write((int) ((c >>> 16) & 0xff));
            out.write((int) ((c >>> 8) & 0xff));
            out.write((int) (c & 0xff));
            return out.toByteArray();
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static void pyWriteRGBPNG(Object path, Object width, Object height, Object pixels) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        byte[] raw = pyToBytes(pixels);
        int expected = w * h * 3;
        if (raw.length != expected) {
            throw new RuntimeException("pixels length mismatch");
        }

        byte[] scan = new byte[h * (1 + w * 3)];
        int rowBytes = w * 3;
        int pos = 0;
        for (int y = 0; y < h; y++) {
            scan[pos++] = 0;
            int start = y * rowBytes;
            System.arraycopy(raw, start, scan, pos, rowBytes);
            pos += rowBytes;
        }

        Deflater deflater = new Deflater(6);
        deflater.setInput(scan);
        deflater.finish();
        byte[] buf = new byte[8192];
        ByteArrayOutputStream zOut = new ByteArrayOutputStream();
        while (!deflater.finished()) {
            int n = deflater.deflate(buf);
            zOut.write(buf, 0, n);
        }
        byte[] idat = zOut.toByteArray();

        byte[] ihdr = new byte[] {
                (byte) (w >>> 24), (byte) (w >>> 16), (byte) (w >>> 8), (byte) w,
                (byte) (h >>> 24), (byte) (h >>> 16), (byte) (h >>> 8), (byte) h,
                8, 2, 0, 0, 0
        };

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            fos.write(new byte[] { (byte) 0x89, 'P', 'N', 'G', '
', '
', 0x1a, '
' });
            fos.write(pyChunk("IHDR", ihdr));
            fos.write(pyChunk("IDAT", idat));
            fos.write(pyChunk("IEND", new byte[0]));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    static byte[] pyLzwEncode(byte[] data, int minCodeSize) {
        if (data.length == 0) {
            return new byte[0];
        }
        int clearCode = 1 << minCodeSize;
        int endCode = clearCode + 1;
        int codeSize = minCodeSize + 1;

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        int bitBuffer = 0;
        int bitCount = 0;
        int[] codes = new int[data.length * 2 + 2];
        int k = 0;
        codes[k++] = clearCode;
        for (byte b : data) {
            codes[k++] = b & 0xff;
            codes[k++] = clearCode;
        }
        codes[k++] = endCode;
        for (int i = 0; i < k; i++) {
            int code = codes[i];
            bitBuffer |= (code << bitCount);
            bitCount += codeSize;
            while (bitCount >= 8) {
                out.write(bitBuffer & 0xff);
                bitBuffer >>>= 8;
                bitCount -= 8;
            }
        }
        if (bitCount > 0) {
            out.write(bitBuffer & 0xff);
        }
        return out.toByteArray();
    }

    static Object pyGrayscalePalette() {
        byte[] p = new byte[256 * 3];
        for (int i = 0; i < 256; i++) {
            p[i * 3] = (byte) i;
            p[i * 3 + 1] = (byte) i;
            p[i * 3 + 2] = (byte) i;
        }
        return p;
    }

    static void pySaveGif(Object path, Object width, Object height, Object frames, Object palette, Object delayCs, Object loop) {
        int w = pyToInt(width);
        int h = pyToInt(height);
        int frameBytes = w * h;
        byte[] pal = pyToBytes(palette);
        if (pal.length != 256 * 3) {
            throw new RuntimeException("palette must be 256*3 bytes");
        }
        int dcs = pyToInt(delayCs);
        int lp = pyToInt(loop);

        List<Object> frs = pyIter(frames);

        try (FileOutputStream fos = new FileOutputStream(pyToString(path))) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            out.write("GIF89a".getBytes(StandardCharsets.US_ASCII));
            out.write(w & 0xff);
            out.write((w >>> 8) & 0xff);
            out.write(h & 0xff);
            out.write((h >>> 8) & 0xff);
            out.write(0xF7);
            out.write(0);
            out.write(0);
            out.write(pal);
            out.write(new byte[] { 0x21, (byte) 0xFF, 0x0B });
            out.write("NETSCAPE2.0".getBytes(StandardCharsets.US_ASCII));
            out.write(new byte[] { 0x03, 0x01, (byte) (lp & 0xff), (byte) ((lp >>> 8) & 0xff), 0x00 });

            for (Object frAny : frs) {
                byte[] fr = pyToBytes(frAny);
                if (fr.length != frameBytes) {
                    throw new RuntimeException("frame size mismatch");
                }
                out.write(new byte[] { 0x21, (byte) 0xF9, 0x04, 0x00, (byte) (dcs & 0xff), (byte) ((dcs >>> 8) & 0xff), 0x00, 0x00 });
                out.write(0x2C);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(0);
                out.write(w & 0xff);
                out.write((w >>> 8) & 0xff);
                out.write(h & 0xff);
                out.write((h >>> 8) & 0xff);
                out.write(0x00);
                out.write(0x08);
                byte[] compressed = pyLzwEncode(fr, 8);
                int pos = 0;
                while (pos < compressed.length) {
                    int len = Math.min(255, compressed.length - pos);
                    out.write(len);
                    out.write(compressed, pos, len);
                    pos += len;
                }
                out.write(0x00);
            }
            out.write(0x3B);
            fos.write(out.toByteArray());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
}

class pytra_16_glass_sculpture_chaos {
    static Object clamp01(Object v) {
        if (PyRuntime.pyBool(PyRuntime.pyLt(v, 0.0))) {
            return 0.0;
        }
        if (PyRuntime.pyBool(PyRuntime.pyGt(v, 1.0))) {
            return 1.0;
        }
        return v;
    }
    static Object dot(Object ax, Object ay, Object az, Object bx, Object by, Object bz) {
        return PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(ax, bx), PyRuntime.pyMul(ay, by)), PyRuntime.pyMul(az, bz));
    }
    static Object length(Object x, Object y, Object z) {
        return PyRuntime.pyMathSqrt(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(x, x), PyRuntime.pyMul(y, y)), PyRuntime.pyMul(z, z)));
    }
    static Object normalize(Object x, Object y, Object z) {
        Object l = length(x, y, z);
        if (PyRuntime.pyBool(PyRuntime.pyLt(l, 1e-09))) {
            return PyRuntime.pyList(0.0, 0.0, 0.0);
        }
        return PyRuntime.pyList(PyRuntime.pyDiv(x, l), PyRuntime.pyDiv(y, l), PyRuntime.pyDiv(z, l));
    }
    static Object reflect(Object ix, Object iy, Object iz, Object nx, Object ny, Object nz) {
        Object d = PyRuntime.pyMul(dot(ix, iy, iz, nx, ny, nz), 2.0);
        return PyRuntime.pyList(PyRuntime.pySub(ix, PyRuntime.pyMul(d, nx)), PyRuntime.pySub(iy, PyRuntime.pyMul(d, ny)), PyRuntime.pySub(iz, PyRuntime.pyMul(d, nz)));
    }
    static Object refract(Object ix, Object iy, Object iz, Object nx, Object ny, Object nz, Object eta) {
        Object cosi = PyRuntime.pyNeg(dot(ix, iy, iz, nx, ny, nz));
        Object sint2 = PyRuntime.pyMul(PyRuntime.pyMul(eta, eta), PyRuntime.pySub(1.0, PyRuntime.pyMul(cosi, cosi)));
        if (PyRuntime.pyBool(PyRuntime.pyGt(sint2, 1.0))) {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        Object cost = PyRuntime.pyMathSqrt(PyRuntime.pySub(1.0, sint2));
        Object k = PyRuntime.pySub(PyRuntime.pyMul(eta, cosi), cost);
        return PyRuntime.pyList(PyRuntime.pyAdd(PyRuntime.pyMul(eta, ix), PyRuntime.pyMul(k, nx)), PyRuntime.pyAdd(PyRuntime.pyMul(eta, iy), PyRuntime.pyMul(k, ny)), PyRuntime.pyAdd(PyRuntime.pyMul(eta, iz), PyRuntime.pyMul(k, nz)));
    }
    static Object schlick(Object cos_theta, Object f0) {
        Object m = PyRuntime.pySub(1.0, cos_theta);
        return PyRuntime.pyAdd(f0, PyRuntime.pyMul(PyRuntime.pySub(1.0, f0), PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(PyRuntime.pyMul(m, m), m), m), m)));
    }
    static Object sky_color(Object dx, Object dy, Object dz, Object tphase) {
        Object t = PyRuntime.pyMul(0.5, PyRuntime.pyAdd(dy, 1.0));
        Object r = PyRuntime.pyAdd(0.06, PyRuntime.pyMul(0.2, t));
        Object g = PyRuntime.pyAdd(0.1, PyRuntime.pyMul(0.25, t));
        Object b = PyRuntime.pyAdd(0.16, PyRuntime.pyMul(0.45, t));
        Object band = PyRuntime.pyAdd(0.5, PyRuntime.pyMul(0.5, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(8.0, dx), PyRuntime.pyMul(6.0, dz)), tphase))));
        r = PyRuntime.pyAdd(r, PyRuntime.pyMul(0.08, band));
        g = PyRuntime.pyAdd(g, PyRuntime.pyMul(0.05, band));
        b = PyRuntime.pyAdd(b, PyRuntime.pyMul(0.12, band));
        return PyRuntime.pyList(clamp01(r), clamp01(g), clamp01(b));
    }
    static Object sphere_intersect(Object ox, Object oy, Object oz, Object dx, Object dy, Object dz, Object cx, Object cy, Object cz, Object radius) {
        Object lx = PyRuntime.pySub(ox, cx);
        Object ly = PyRuntime.pySub(oy, cy);
        Object lz = PyRuntime.pySub(oz, cz);
        Object b = PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lx, dx), PyRuntime.pyMul(ly, dy)), PyRuntime.pyMul(lz, dz));
        Object c = PyRuntime.pySub(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lx, lx), PyRuntime.pyMul(ly, ly)), PyRuntime.pyMul(lz, lz)), PyRuntime.pyMul(radius, radius));
        Object h = PyRuntime.pySub(PyRuntime.pyMul(b, b), c);
        if (PyRuntime.pyBool(PyRuntime.pyLt(h, 0.0))) {
            return PyRuntime.pyNeg(1.0);
        }
        Object s = PyRuntime.pyMathSqrt(h);
        Object t0 = PyRuntime.pySub(PyRuntime.pyNeg(b), s);
        if (PyRuntime.pyBool(PyRuntime.pyGt(t0, 0.0001))) {
            return t0;
        }
        Object t1 = PyRuntime.pyAdd(PyRuntime.pyNeg(b), s);
        if (PyRuntime.pyBool(PyRuntime.pyGt(t1, 0.0001))) {
            return t1;
        }
        return PyRuntime.pyNeg(1.0);
    }
    static Object palette_332() {
        Object p = PyRuntime.pyBytearray(PyRuntime.pyMul(256, 3));
        Object i = null;
        for (Object __pytra_it_1 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(256), PyRuntime.pyToInt(1))) {
            i = __pytra_it_1;
            Object r = PyRuntime.pyBitAnd(PyRuntime.pyRShift(i, 5), 7);
            Object g = PyRuntime.pyBitAnd(PyRuntime.pyRShift(i, 2), 7);
            Object b = PyRuntime.pyBitAnd(i, 3);
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 0), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, r), 7)));
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 1), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, g), 7)));
            PyRuntime.pySet(p, PyRuntime.pyAdd(PyRuntime.pyMul(i, 3), 2), PyRuntime.pyToInt(PyRuntime.pyDiv(PyRuntime.pyMul(255, b), 3)));
        }
        return PyRuntime.pyBytes(p);
    }
    static Object quantize_332(Object r, Object g, Object b) {
        Object rr = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(r), 255.0));
        Object gg = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(g), 255.0));
        Object bb = PyRuntime.pyToInt(PyRuntime.pyMul(clamp01(b), 255.0));
        return PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyLShift(PyRuntime.pyRShift(rr, 5), 5), PyRuntime.pyLShift(PyRuntime.pyRShift(gg, 5), 2)), PyRuntime.pyRShift(bb, 6));
    }
    static Object render_frame(Object width, Object height, Object frame_id, Object frames_n) {
        Object t = PyRuntime.pyDiv(frame_id, frames_n);
        Object tphase = PyRuntime.pyMul(PyRuntime.pyMul(2.0, PyRuntime.pyMathPi()), t);
        Object cam_r = 3.0;
        Object cam_x = PyRuntime.pyMul(cam_r, PyRuntime.pyMathCos(PyRuntime.pyMul(tphase, 0.9)));
        Object cam_y = PyRuntime.pyAdd(1.1, PyRuntime.pyMul(0.25, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 0.6))));
        Object cam_z = PyRuntime.pyMul(cam_r, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 0.9)));
        Object look_x = 0.0;
        Object look_y = 0.35;
        Object look_z = 0.0;
        Object __pytra_tuple_2 = normalize(PyRuntime.pySub(look_x, cam_x), PyRuntime.pySub(look_y, cam_y), PyRuntime.pySub(look_z, cam_z));
        Object fwd_x = PyRuntime.pyGet(__pytra_tuple_2, 0);
        Object fwd_y = PyRuntime.pyGet(__pytra_tuple_2, 1);
        Object fwd_z = PyRuntime.pyGet(__pytra_tuple_2, 2);
        Object __pytra_tuple_3 = normalize(fwd_z, 0.0, PyRuntime.pyNeg(fwd_x));
        Object right_x = PyRuntime.pyGet(__pytra_tuple_3, 0);
        Object right_y = PyRuntime.pyGet(__pytra_tuple_3, 1);
        Object right_z = PyRuntime.pyGet(__pytra_tuple_3, 2);
        Object __pytra_tuple_4 = normalize(PyRuntime.pySub(PyRuntime.pyMul(right_y, fwd_z), PyRuntime.pyMul(right_z, fwd_y)), PyRuntime.pySub(PyRuntime.pyMul(right_z, fwd_x), PyRuntime.pyMul(right_x, fwd_z)), PyRuntime.pySub(PyRuntime.pyMul(right_x, fwd_y), PyRuntime.pyMul(right_y, fwd_x)));
        Object up_x = PyRuntime.pyGet(__pytra_tuple_4, 0);
        Object up_y = PyRuntime.pyGet(__pytra_tuple_4, 1);
        Object up_z = PyRuntime.pyGet(__pytra_tuple_4, 2);
        Object s0x = PyRuntime.pyMul(0.9, PyRuntime.pyMathCos(PyRuntime.pyMul(1.3, tphase)));
        Object s0y = PyRuntime.pyAdd(0.15, PyRuntime.pyMul(0.35, PyRuntime.pyMathSin(PyRuntime.pyMul(1.7, tphase))));
        Object s0z = PyRuntime.pyMul(0.9, PyRuntime.pyMathSin(PyRuntime.pyMul(1.3, tphase)));
        Object s1x = PyRuntime.pyMul(1.2, PyRuntime.pyMathCos(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 2.094)));
        Object s1y = PyRuntime.pyAdd(0.1, PyRuntime.pyMul(0.4, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.1, tphase), 0.8))));
        Object s1z = PyRuntime.pyMul(1.2, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 2.094)));
        Object s2x = PyRuntime.pyMul(1.0, PyRuntime.pyMathCos(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 4.188)));
        Object s2y = PyRuntime.pyAdd(0.2, PyRuntime.pyMul(0.3, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.5, tphase), 1.9))));
        Object s2z = PyRuntime.pyMul(1.0, PyRuntime.pyMathSin(PyRuntime.pyAdd(PyRuntime.pyMul(1.3, tphase), 4.188)));
        Object lr = 0.35;
        Object lx = PyRuntime.pyMul(2.4, PyRuntime.pyMathCos(PyRuntime.pyMul(tphase, 1.8)));
        Object ly = PyRuntime.pyAdd(1.8, PyRuntime.pyMul(0.8, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 1.2))));
        Object lz = PyRuntime.pyMul(2.4, PyRuntime.pyMathSin(PyRuntime.pyMul(tphase, 1.8)));
        Object frame = PyRuntime.pyBytearray(PyRuntime.pyMul(width, height));
        Object aspect = PyRuntime.pyDiv(width, height);
        Object fov = 1.25;
        Object i = 0;
        Object py = null;
        for (Object __pytra_it_5 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(height), PyRuntime.pyToInt(1))) {
            py = __pytra_it_5;
            Object sy = PyRuntime.pySub(1.0, PyRuntime.pyDiv(PyRuntime.pyMul(2.0, PyRuntime.pyAdd(py, 0.5)), height));
            Object px = null;
            for (Object __pytra_it_6 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(width), PyRuntime.pyToInt(1))) {
                px = __pytra_it_6;
                Object sx = PyRuntime.pyMul(PyRuntime.pySub(PyRuntime.pyDiv(PyRuntime.pyMul(2.0, PyRuntime.pyAdd(px, 0.5)), width), 1.0), aspect);
                Object rx = PyRuntime.pyAdd(fwd_x, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_x), PyRuntime.pyMul(sy, up_x))));
                Object ry = PyRuntime.pyAdd(fwd_y, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_y), PyRuntime.pyMul(sy, up_y))));
                Object rz = PyRuntime.pyAdd(fwd_z, PyRuntime.pyMul(fov, PyRuntime.pyAdd(PyRuntime.pyMul(sx, right_z), PyRuntime.pyMul(sy, up_z))));
                Object __pytra_tuple_7 = normalize(rx, ry, rz);
                Object dx = PyRuntime.pyGet(__pytra_tuple_7, 0);
                Object dy = PyRuntime.pyGet(__pytra_tuple_7, 1);
                Object dz = PyRuntime.pyGet(__pytra_tuple_7, 2);
                Object best_t = 1000000000.0;
                Object hit_kind = 0;
                Object r = 0.0;
                Object g = 0.0;
                Object b = 0.0;
                if (PyRuntime.pyBool(PyRuntime.pyLt(dy, PyRuntime.pyNeg(1e-06)))) {
                    Object tf = PyRuntime.pyDiv(PyRuntime.pySub(PyRuntime.pyNeg(1.2), cam_y), dy);
                    if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(tf, 0.0001)) && PyRuntime.pyBool(PyRuntime.pyLt(tf, best_t))))) {
                        best_t = tf;
                        hit_kind = 1;
                    }
                }
                Object t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t0, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t0, best_t))))) {
                    best_t = t0;
                    hit_kind = 2;
                }
                Object t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t1, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t1, best_t))))) {
                    best_t = t1;
                    hit_kind = 3;
                }
                Object t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if (PyRuntime.pyBool((PyRuntime.pyBool(PyRuntime.pyGt(t2, 0.0)) && PyRuntime.pyBool(PyRuntime.pyLt(t2, best_t))))) {
                    best_t = t2;
                    hit_kind = 4;
                }
                if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 0))) {
                    Object __pytra_tuple_8 = sky_color(dx, dy, dz, tphase);
                    r = PyRuntime.pyGet(__pytra_tuple_8, 0);
                    g = PyRuntime.pyGet(__pytra_tuple_8, 1);
                    b = PyRuntime.pyGet(__pytra_tuple_8, 2);
                } else {
                    if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 1))) {
                        Object hx = PyRuntime.pyAdd(cam_x, PyRuntime.pyMul(best_t, dx));
                        Object hz = PyRuntime.pyAdd(cam_z, PyRuntime.pyMul(best_t, dz));
                        Object cx = PyRuntime.pyToInt(PyRuntime.pyMathFloor(PyRuntime.pyMul(hx, 2.0)));
                        Object cz = PyRuntime.pyToInt(PyRuntime.pyMathFloor(PyRuntime.pyMul(hz, 2.0)));
                        Object checker = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(PyRuntime.pyMod(PyRuntime.pyAdd(cx, cz), 2), 0)), 0, 1);
                        Object base_r = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.1, 0.04);
                        Object base_g = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.11, 0.05);
                        Object base_b = PyRuntime.pyTernary(PyRuntime.pyBool(PyRuntime.pyEq(checker, 0)), 0.13, 0.08);
                        Object lxv = PyRuntime.pySub(lx, hx);
                        Object lyv = PyRuntime.pySub(ly, PyRuntime.pyNeg(1.2));
                        Object lzv = PyRuntime.pySub(lz, hz);
                        Object __pytra_tuple_9 = normalize(lxv, lyv, lzv);
                        Object ldx = PyRuntime.pyGet(__pytra_tuple_9, 0);
                        Object ldy = PyRuntime.pyGet(__pytra_tuple_9, 1);
                        Object ldz = PyRuntime.pyGet(__pytra_tuple_9, 2);
                        Object ndotl = PyRuntime.pyMax(ldy, 0.0);
                        Object ldist2 = PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(lxv, lxv), PyRuntime.pyMul(lyv, lyv)), PyRuntime.pyMul(lzv, lzv));
                        Object glow = PyRuntime.pyDiv(8.0, PyRuntime.pyAdd(1.0, ldist2));
                        r = PyRuntime.pyAdd(PyRuntime.pyAdd(base_r, PyRuntime.pyMul(0.8, glow)), PyRuntime.pyMul(0.2, ndotl));
                        g = PyRuntime.pyAdd(PyRuntime.pyAdd(base_g, PyRuntime.pyMul(0.5, glow)), PyRuntime.pyMul(0.18, ndotl));
                        b = PyRuntime.pyAdd(PyRuntime.pyAdd(base_b, PyRuntime.pyMul(1.0, glow)), PyRuntime.pyMul(0.24, ndotl));
                    } else {
                        Object cx = 0.0;
                        Object cy = 0.0;
                        Object cz = 0.0;
                        Object rad = 1.0;
                        if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 2))) {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        } else {
                            if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 3))) {
                                cx = s1x;
                                cy = s1y;
                                cz = s1z;
                                rad = 0.72;
                            } else {
                                cx = s2x;
                                cy = s2y;
                                cz = s2z;
                                rad = 0.58;
                            }
                        }
                        Object hx = PyRuntime.pyAdd(cam_x, PyRuntime.pyMul(best_t, dx));
                        Object hy = PyRuntime.pyAdd(cam_y, PyRuntime.pyMul(best_t, dy));
                        Object hz = PyRuntime.pyAdd(cam_z, PyRuntime.pyMul(best_t, dz));
                        Object __pytra_tuple_10 = normalize(PyRuntime.pyDiv(PyRuntime.pySub(hx, cx), rad), PyRuntime.pyDiv(PyRuntime.pySub(hy, cy), rad), PyRuntime.pyDiv(PyRuntime.pySub(hz, cz), rad));
                        Object nx = PyRuntime.pyGet(__pytra_tuple_10, 0);
                        Object ny = PyRuntime.pyGet(__pytra_tuple_10, 1);
                        Object nz = PyRuntime.pyGet(__pytra_tuple_10, 2);
                        Object __pytra_tuple_11 = reflect(dx, dy, dz, nx, ny, nz);
                        Object rdx = PyRuntime.pyGet(__pytra_tuple_11, 0);
                        Object rdy = PyRuntime.pyGet(__pytra_tuple_11, 1);
                        Object rdz = PyRuntime.pyGet(__pytra_tuple_11, 2);
                        Object __pytra_tuple_12 = refract(dx, dy, dz, nx, ny, nz, PyRuntime.pyDiv(1.0, 1.45));
                        Object tdx = PyRuntime.pyGet(__pytra_tuple_12, 0);
                        Object tdy = PyRuntime.pyGet(__pytra_tuple_12, 1);
                        Object tdz = PyRuntime.pyGet(__pytra_tuple_12, 2);
                        Object __pytra_tuple_13 = sky_color(rdx, rdy, rdz, tphase);
                        Object sr = PyRuntime.pyGet(__pytra_tuple_13, 0);
                        Object sg = PyRuntime.pyGet(__pytra_tuple_13, 1);
                        Object sb = PyRuntime.pyGet(__pytra_tuple_13, 2);
                        Object __pytra_tuple_14 = sky_color(tdx, tdy, tdz, PyRuntime.pyAdd(tphase, 0.8));
                        Object tr = PyRuntime.pyGet(__pytra_tuple_14, 0);
                        Object tg = PyRuntime.pyGet(__pytra_tuple_14, 1);
                        Object tb = PyRuntime.pyGet(__pytra_tuple_14, 2);
                        Object cosi = PyRuntime.pyMax(PyRuntime.pyNeg(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(dx, nx), PyRuntime.pyMul(dy, ny)), PyRuntime.pyMul(dz, nz))), 0.0);
                        Object fr = schlick(cosi, 0.04);
                        r = PyRuntime.pyAdd(PyRuntime.pyMul(tr, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sr, fr));
                        g = PyRuntime.pyAdd(PyRuntime.pyMul(tg, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sg, fr));
                        b = PyRuntime.pyAdd(PyRuntime.pyMul(tb, PyRuntime.pySub(1.0, fr)), PyRuntime.pyMul(sb, fr));
                        Object lxv = PyRuntime.pySub(lx, hx);
                        Object lyv = PyRuntime.pySub(ly, hy);
                        Object lzv = PyRuntime.pySub(lz, hz);
                        Object __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                        Object ldx = PyRuntime.pyGet(__pytra_tuple_15, 0);
                        Object ldy = PyRuntime.pyGet(__pytra_tuple_15, 1);
                        Object ldz = PyRuntime.pyGet(__pytra_tuple_15, 2);
                        Object ndotl = PyRuntime.pyMax(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(nx, ldx), PyRuntime.pyMul(ny, ldy)), PyRuntime.pyMul(nz, ldz)), 0.0);
                        Object __pytra_tuple_16 = normalize(PyRuntime.pySub(ldx, dx), PyRuntime.pySub(ldy, dy), PyRuntime.pySub(ldz, dz));
                        Object hvx = PyRuntime.pyGet(__pytra_tuple_16, 0);
                        Object hvy = PyRuntime.pyGet(__pytra_tuple_16, 1);
                        Object hvz = PyRuntime.pyGet(__pytra_tuple_16, 2);
                        Object ndoth = PyRuntime.pyMax(PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(nx, hvx), PyRuntime.pyMul(ny, hvy)), PyRuntime.pyMul(nz, hvz)), 0.0);
                        Object spec = PyRuntime.pyMul(ndoth, ndoth);
                        spec = PyRuntime.pyMul(spec, spec);
                        spec = PyRuntime.pyMul(spec, spec);
                        spec = PyRuntime.pyMul(spec, spec);
                        Object glow = PyRuntime.pyDiv(10.0, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyAdd(1.0, PyRuntime.pyMul(lxv, lxv)), PyRuntime.pyMul(lyv, lyv)), PyRuntime.pyMul(lzv, lzv)));
                        r = PyRuntime.pyAdd(r, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.2, ndotl), PyRuntime.pyMul(0.8, spec)), PyRuntime.pyMul(0.45, glow)));
                        g = PyRuntime.pyAdd(g, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.18, ndotl), PyRuntime.pyMul(0.6, spec)), PyRuntime.pyMul(0.35, glow)));
                        b = PyRuntime.pyAdd(b, PyRuntime.pyAdd(PyRuntime.pyAdd(PyRuntime.pyMul(0.26, ndotl), PyRuntime.pyMul(1.0, spec)), PyRuntime.pyMul(0.65, glow)));
                        if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 2))) {
                            r = PyRuntime.pyMul(r, 0.95);
                            g = PyRuntime.pyMul(g, 1.05);
                            b = PyRuntime.pyMul(b, 1.1);
                        } else {
                            if (PyRuntime.pyBool(PyRuntime.pyEq(hit_kind, 3))) {
                                r = PyRuntime.pyMul(r, 1.08);
                                g = PyRuntime.pyMul(g, 0.98);
                                b = PyRuntime.pyMul(b, 1.04);
                            } else {
                                r = PyRuntime.pyMul(r, 1.02);
                                g = PyRuntime.pyMul(g, 1.1);
                                b = PyRuntime.pyMul(b, 0.95);
                            }
                        }
                    }
                }
                r = PyRuntime.pyMathSqrt(clamp01(r));
                g = PyRuntime.pyMathSqrt(clamp01(g));
                b = PyRuntime.pyMathSqrt(clamp01(b));
                PyRuntime.pySet(frame, i, quantize_332(r, g, b));
                i = PyRuntime.pyAdd(i, 1);
            }
        }
        return PyRuntime.pyBytes(frame);
    }
    static Object run_16_glass_sculpture_chaos() {
        Object width = 320;
        Object height = 240;
        Object frames_n = 72;
        Object out_path = "sample/out/16_glass_sculpture_chaos.gif";
        Object start = PyRuntime.pyPerfCounter();
        Object frames = PyRuntime.pyList();
        Object i = null;
        for (Object __pytra_it_17 : PyRuntime.pyRange(PyRuntime.pyToInt(0), PyRuntime.pyToInt(frames_n), PyRuntime.pyToInt(1))) {
            i = __pytra_it_17;
            ((java.util.List<Object>)frames).add(render_frame(width, height, i, frames_n));
        }
        PyRuntime.pySaveGif(out_path, width, height, frames, palette_332(), 6, 0);
        Object elapsed = PyRuntime.pySub(PyRuntime.pyPerfCounter(), start);
        PyRuntime.pyPrint("output:", out_path);
        PyRuntime.pyPrint("frames:", frames_n);
        PyRuntime.pyPrint("elapsed_sec:", elapsed);
        return null;
    }

    public static void main(String[] args) {
        run_16_glass_sculpture_chaos();
    }
}
```
</details>

<details>
<summary>Swiftへの変換例 : 16_glass_sculpture_chaos.swift</summary>

```swift
// このファイルは自動生成です（Python -> Swift node-backed mode）。

// Swift 実行向け Node.js ランタイム補助。

import Foundation

/// Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
/// - Parameters:
///   - sourceBase64: JavaScript ソースコードの Base64 文字列。
///   - args: JavaScript 側へ渡す引数配列。
/// - Returns:
///   node プロセスの終了コード。失敗時は 1 を返す。
func pytraRunEmbeddedNode(_ sourceBase64: String, _ args: [String]) -> Int32 {
    guard let sourceData = Data(base64Encoded: sourceBase64) else {
        fputs("error: failed to decode embedded JavaScript source
", stderr)
        return 1
    }

    let tmpDir = URL(fileURLWithPath: NSTemporaryDirectory(), isDirectory: true)
    let fileName = "pytra_embedded_\(UUID().uuidString).js"
    let scriptURL = tmpDir.appendingPathComponent(fileName)

    do {
        try sourceData.write(to: scriptURL)
    } catch {
        fputs("error: failed to write temporary JavaScript file: \(error)
", stderr)
        return 1
    }

    let process = Process()
    process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    process.arguments = ["node", scriptURL.path] + args
    process.environment = ProcessInfo.processInfo.environment
    process.standardInput = FileHandle.standardInput
    process.standardOutput = FileHandle.standardOutput
    process.standardError = FileHandle.standardError

    do {
        try process.run()
        process.waitUntilExit()
    } catch {
        fputs("error: failed to launch node: \(error)
", stderr)
        try? FileManager.default.removeItem(at: scriptURL)
        return 1
    }

    try? FileManager.default.removeItem(at: scriptURL)
    return process.terminationStatus
}

// 埋め込み JavaScript ソース（Base64）。
let pytraEmbeddedJsBase64 = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24gY2xhbXAwMSh2KSB7CiAgICBpZiAocHlCb29sKCgodikgPCAoMC4wKSkpKSB7CiAgICAgICAgcmV0dXJuIDAuMDsKICAgIH0KICAgIGlmIChweUJvb2woKCh2KSA+ICgxLjApKSkpIHsKICAgICAgICByZXR1cm4gMS4wOwogICAgfQogICAgcmV0dXJuIHY7Cn0KZnVuY3Rpb24gZG90KGF4LCBheSwgYXosIGJ4LCBieSwgYnopIHsKICAgIHJldHVybiAoKCgoKChheCkgKiAoYngpKSkgKyAoKChheSkgKiAoYnkpKSkpKSArICgoKGF6KSAqIChieikpKSk7Cn0KZnVuY3Rpb24gbGVuZ3RoKHgsIHksIHopIHsKICAgIHJldHVybiBtYXRoLnNxcnQoKCgoKCgoeCkgKiAoeCkpKSArICgoKHkpICogKHkpKSkpKSArICgoKHopICogKHopKSkpKTsKfQpmdW5jdGlvbiBub3JtYWxpemUoeCwgeSwgeikgewogICAgbGV0IGwgPSBsZW5ndGgoeCwgeSwgeik7CiAgICBpZiAocHlCb29sKCgobCkgPCAoMWUtMDkpKSkpIHsKICAgICAgICByZXR1cm4gWzAuMCwgMC4wLCAwLjBdOwogICAgfQogICAgcmV0dXJuIFsoKHgpIC8gKGwpKSwgKCh5KSAvIChsKSksICgoeikgLyAobCkpXTsKfQpmdW5jdGlvbiByZWZsZWN0KGl4LCBpeSwgaXosIG54LCBueSwgbnopIHsKICAgIGxldCBkID0gKChkb3QoaXgsIGl5LCBpeiwgbngsIG55LCBueikpICogKDIuMCkpOwogICAgcmV0dXJuIFsoKGl4KSAtICgoKGQpICogKG54KSkpKSwgKChpeSkgLSAoKChkKSAqIChueSkpKSksICgoaXopIC0gKCgoZCkgKiAobnopKSkpXTsKfQpmdW5jdGlvbiByZWZyYWN0KGl4LCBpeSwgaXosIG54LCBueSwgbnosIGV0YSkgewogICAgbGV0IGNvc2kgPSAoLShkb3QoaXgsIGl5LCBpeiwgbngsIG55LCBueikpKTsKICAgIGxldCBzaW50MiA9ICgoKChldGEpICogKGV0YSkpKSAqICgoKDEuMCkgLSAoKChjb3NpKSAqIChjb3NpKSkpKSkpOwogICAgaWYgKHB5Qm9vbCgoKHNpbnQyKSA+ICgxLjApKSkpIHsKICAgICAgICByZXR1cm4gcmVmbGVjdChpeCwgaXksIGl6LCBueCwgbnksIG56KTsKICAgIH0KICAgIGxldCBjb3N0ID0gbWF0aC5zcXJ0KCgoMS4wKSAtIChzaW50MikpKTsKICAgIGxldCBrID0gKCgoKGV0YSkgKiAoY29zaSkpKSAtIChjb3N0KSk7CiAgICByZXR1cm4gWygoKChldGEpICogKGl4KSkpICsgKCgoaykgKiAobngpKSkpLCAoKCgoZXRhKSAqIChpeSkpKSArICgoKGspICogKG55KSkpKSwgKCgoKGV0YSkgKiAoaXopKSkgKyAoKChrKSAqIChueikpKSldOwp9CmZ1bmN0aW9uIHNjaGxpY2soY29zX3RoZXRhLCBmMCkgewogICAgbGV0IG0gPSAoKDEuMCkgLSAoY29zX3RoZXRhKSk7CiAgICByZXR1cm4gKChmMCkgKyAoKCgoKDEuMCkgLSAoZjApKSkgKiAoKCgoKCgoKChtKSAqIChtKSkpICogKG0pKSkgKiAobSkpKSAqIChtKSkpKSkpOwp9CmZ1bmN0aW9uIHNreV9jb2xvcihkeCwgZHksIGR6LCB0cGhhc2UpIHsKICAgIGxldCB0ID0gKCgwLjUpICogKCgoZHkpICsgKDEuMCkpKSk7CiAgICBsZXQgciA9ICgoMC4wNikgKyAoKCgwLjIpICogKHQpKSkpOwogICAgbGV0IGcgPSAoKDAuMSkgKyAoKCgwLjI1KSAqICh0KSkpKTsKICAgIGxldCBiID0gKCgwLjE2KSArICgoKDAuNDUpICogKHQpKSkpOwogICAgbGV0IGJhbmQgPSAoKDAuNSkgKyAoKCgwLjUpICogKG1hdGguc2luKCgoKCgoKDguMCkgKiAoZHgpKSkgKyAoKCg2LjApICogKGR6KSkpKSkgKyAodHBoYXNlKSkpKSkpKTsKICAgIHIgPSByICsgKCgwLjA4KSAqIChiYW5kKSk7CiAgICBnID0gZyArICgoMC4wNSkgKiAoYmFuZCkpOwogICAgYiA9IGIgKyAoKDAuMTIpICogKGJhbmQpKTsKICAgIHJldHVybiBbY2xhbXAwMShyKSwgY2xhbXAwMShnKSwgY2xhbXAwMShiKV07Cn0KZnVuY3Rpb24gc3BoZXJlX2ludGVyc2VjdChveCwgb3ksIG96LCBkeCwgZHksIGR6LCBjeCwgY3ksIGN6LCByYWRpdXMpIHsKICAgIGxldCBseCA9ICgob3gpIC0gKGN4KSk7CiAgICBsZXQgbHkgPSAoKG95KSAtIChjeSkpOwogICAgbGV0IGx6ID0gKChveikgLSAoY3opKTsKICAgIGxldCBiID0gKCgoKCgobHgpICogKGR4KSkpICsgKCgobHkpICogKGR5KSkpKSkgKyAoKChseikgKiAoZHopKSkpOwogICAgbGV0IGMgPSAoKCgoKCgoKGx4KSAqIChseCkpKSArICgoKGx5KSAqIChseSkpKSkpICsgKCgobHopICogKGx6KSkpKSkgLSAoKChyYWRpdXMpICogKHJhZGl1cykpKSk7CiAgICBsZXQgaCA9ICgoKChiKSAqIChiKSkpIC0gKGMpKTsKICAgIGlmIChweUJvb2woKChoKSA8ICgwLjApKSkpIHsKICAgICAgICByZXR1cm4gKC0oMS4wKSk7CiAgICB9CiAgICBsZXQgcyA9IG1hdGguc3FydChoKTsKICAgIGxldCB0MCA9ICgoKC0oYikpKSAtIChzKSk7CiAgICBpZiAocHlCb29sKCgodDApID4gKDAuMDAwMSkpKSkgewogICAgICAgIHJldHVybiB0MDsKICAgIH0KICAgIGxldCB0MSA9ICgoKC0oYikpKSArIChzKSk7CiAgICBpZiAocHlCb29sKCgodDEpID4gKDAuMDAwMSkpKSkgewogICAgICAgIHJldHVybiB0MTsKICAgIH0KICAgIHJldHVybiAoLSgxLjApKTsKfQpmdW5jdGlvbiBwYWxldHRlXzMzMigpIHsKICAgIGxldCBwID0gcHlCeXRlYXJyYXkoKCgyNTYpICogKDMpKSk7CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMDsgX19weXRyYV9pXzEgPCAyNTY7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHIgPSAoKCgoaSkgPj4gKDUpKSkgJiAoNykpOwogICAgICAgIGxldCBnID0gKCgoKGkpID4+ICgyKSkpICYgKDcpKTsKICAgICAgICBsZXQgYiA9ICgoaSkgJiAoMykpOwogICAgICAgIHBbKCgoKGkpICogKDMpKSkgKyAoMCkpXSA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCgyNTUpICogKHIpKSkgLyAoNykpKSk7CiAgICAgICAgcFsoKCgoaSkgKiAoMykpKSArICgxKSldID0gTWF0aC50cnVuYyhOdW1iZXIoKCgoKDI1NSkgKiAoZykpKSAvICg3KSkpKTsKICAgICAgICBwWygoKChpKSAqICgzKSkpICsgKDIpKV0gPSBNYXRoLnRydW5jKE51bWJlcigoKCgoMjU1KSAqIChiKSkpIC8gKDMpKSkpOwogICAgfQogICAgcmV0dXJuIHB5Qnl0ZXMocCk7Cn0KZnVuY3Rpb24gcXVhbnRpemVfMzMyKHIsIGcsIGIpIHsKICAgIGxldCByciA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoY2xhbXAwMShyKSkgKiAoMjU1LjApKSkpOwogICAgbGV0IGdnID0gTWF0aC50cnVuYyhOdW1iZXIoKChjbGFtcDAxKGcpKSAqICgyNTUuMCkpKSk7CiAgICBsZXQgYmIgPSBNYXRoLnRydW5jKE51bWJlcigoKGNsYW1wMDEoYikpICogKDI1NS4wKSkpKTsKICAgIHJldHVybiAoKCgoKCgoKHJyKSA+PiAoNSkpKSA8PCAoNSkpKSArICgoKCgoZ2cpID4+ICg1KSkpIDw8ICgyKSkpKSkgKyAoKChiYikgPj4gKDYpKSkpOwp9CmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBmcmFtZV9pZCwgZnJhbWVzX24pIHsKICAgIGxldCB0ID0gKChmcmFtZV9pZCkgLyAoZnJhbWVzX24pKTsKICAgIGxldCB0cGhhc2UgPSAoKCgoMi4wKSAqIChtYXRoLnBpKSkpICogKHQpKTsKICAgIGxldCBjYW1fciA9IDMuMDsKICAgIGxldCBjYW1feCA9ICgoY2FtX3IpICogKG1hdGguY29zKCgodHBoYXNlKSAqICgwLjkpKSkpKTsKICAgIGxldCBjYW1feSA9ICgoMS4xKSArICgoKDAuMjUpICogKG1hdGguc2luKCgodHBoYXNlKSAqICgwLjYpKSkpKSkpOwogICAgbGV0IGNhbV96ID0gKChjYW1fcikgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDAuOSkpKSkpOwogICAgbGV0IGxvb2tfeCA9IDAuMDsKICAgIGxldCBsb29rX3kgPSAwLjM1OwogICAgbGV0IGxvb2tfeiA9IDAuMDsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfMiA9IG5vcm1hbGl6ZSgoKGxvb2tfeCkgLSAoY2FtX3gpKSwgKChsb29rX3kpIC0gKGNhbV95KSksICgobG9va196KSAtIChjYW1feikpKTsKICAgIGxldCBmd2RfeCA9IF9fcHl0cmFfdHVwbGVfMlswXTsKICAgIGxldCBmd2RfeSA9IF9fcHl0cmFfdHVwbGVfMlsxXTsKICAgIGxldCBmd2RfeiA9IF9fcHl0cmFfdHVwbGVfMlsyXTsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfMyA9IG5vcm1hbGl6ZShmd2RfeiwgMC4wLCAoLShmd2RfeCkpKTsKICAgIGxldCByaWdodF94ID0gX19weXRyYV90dXBsZV8zWzBdOwogICAgbGV0IHJpZ2h0X3kgPSBfX3B5dHJhX3R1cGxlXzNbMV07CiAgICBsZXQgcmlnaHRfeiA9IF9fcHl0cmFfdHVwbGVfM1syXTsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfNCA9IG5vcm1hbGl6ZSgoKCgocmlnaHRfeSkgKiAoZndkX3opKSkgLSAoKChyaWdodF96KSAqIChmd2RfeSkpKSksICgoKChyaWdodF96KSAqIChmd2RfeCkpKSAtICgoKHJpZ2h0X3gpICogKGZ3ZF96KSkpKSwgKCgoKHJpZ2h0X3gpICogKGZ3ZF95KSkpIC0gKCgocmlnaHRfeSkgKiAoZndkX3gpKSkpKTsKICAgIGxldCB1cF94ID0gX19weXRyYV90dXBsZV80WzBdOwogICAgbGV0IHVwX3kgPSBfX3B5dHJhX3R1cGxlXzRbMV07CiAgICBsZXQgdXBfeiA9IF9fcHl0cmFfdHVwbGVfNFsyXTsKICAgIGxldCBzMHggPSAoKDAuOSkgKiAobWF0aC5jb3MoKCgxLjMpICogKHRwaGFzZSkpKSkpOwogICAgbGV0IHMweSA9ICgoMC4xNSkgKyAoKCgwLjM1KSAqIChtYXRoLnNpbigoKDEuNykgKiAodHBoYXNlKSkpKSkpKTsKICAgIGxldCBzMHogPSAoKDAuOSkgKiAobWF0aC5zaW4oKCgxLjMpICogKHRwaGFzZSkpKSkpOwogICAgbGV0IHMxeCA9ICgoMS4yKSAqIChtYXRoLmNvcygoKCgoMS4zKSAqICh0cGhhc2UpKSkgKyAoMi4wOTQpKSkpKTsKICAgIGxldCBzMXkgPSAoKDAuMSkgKyAoKCgwLjQpICogKG1hdGguc2luKCgoKCgxLjEpICogKHRwaGFzZSkpKSArICgwLjgpKSkpKSkpOwogICAgbGV0IHMxeiA9ICgoMS4yKSAqIChtYXRoLnNpbigoKCgoMS4zKSAqICh0cGhhc2UpKSkgKyAoMi4wOTQpKSkpKTsKICAgIGxldCBzMnggPSAoKDEuMCkgKiAobWF0aC5jb3MoKCgoKDEuMykgKiAodHBoYXNlKSkpICsgKDQuMTg4KSkpKSk7CiAgICBsZXQgczJ5ID0gKCgwLjIpICsgKCgoMC4zKSAqIChtYXRoLnNpbigoKCgoMS41KSAqICh0cGhhc2UpKSkgKyAoMS45KSkpKSkpKTsKICAgIGxldCBzMnogPSAoKDEuMCkgKiAobWF0aC5zaW4oKCgoKDEuMykgKiAodHBoYXNlKSkpICsgKDQuMTg4KSkpKSk7CiAgICBsZXQgbHIgPSAwLjM1OwogICAgbGV0IGx4ID0gKCgyLjQpICogKG1hdGguY29zKCgodHBoYXNlKSAqICgxLjgpKSkpKTsKICAgIGxldCBseSA9ICgoMS44KSArICgoKDAuOCkgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDEuMikpKSkpKSk7CiAgICBsZXQgbHogPSAoKDIuNCkgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDEuOCkpKSkpOwogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGFzcGVjdCA9ICgod2lkdGgpIC8gKGhlaWdodCkpOwogICAgbGV0IGZvdiA9IDEuMjU7CiAgICBsZXQgaSA9IDA7CiAgICBsZXQgcHk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfNSA9IDA7IF9fcHl0cmFfaV81IDwgaGVpZ2h0OyBfX3B5dHJhX2lfNSArPSAxKSB7CiAgICAgICAgcHkgPSBfX3B5dHJhX2lfNTsKICAgICAgICBsZXQgc3kgPSAoKDEuMCkgLSAoKCgoKDIuMCkgKiAoKChweSkgKyAoMC41KSkpKSkgLyAoaGVpZ2h0KSkpKTsKICAgICAgICBsZXQgcHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzYgPSAwOyBfX3B5dHJhX2lfNiA8IHdpZHRoOyBfX3B5dHJhX2lfNiArPSAxKSB7CiAgICAgICAgICAgIHB4ID0gX19weXRyYV9pXzY7CiAgICAgICAgICAgIGxldCBzeCA9ICgoKCgoKCgoMi4wKSAqICgoKHB4KSArICgwLjUpKSkpKSAvICh3aWR0aCkpKSAtICgxLjApKSkgKiAoYXNwZWN0KSk7CiAgICAgICAgICAgIGxldCByeCA9ICgoZndkX3gpICsgKCgoZm92KSAqICgoKCgoc3gpICogKHJpZ2h0X3gpKSkgKyAoKChzeSkgKiAodXBfeCkpKSkpKSkpOwogICAgICAgICAgICBsZXQgcnkgPSAoKGZ3ZF95KSArICgoKGZvdikgKiAoKCgoKHN4KSAqIChyaWdodF95KSkpICsgKCgoc3kpICogKHVwX3kpKSkpKSkpKTsKICAgICAgICAgICAgbGV0IHJ6ID0gKChmd2RfeikgKyAoKChmb3YpICogKCgoKChzeCkgKiAocmlnaHRfeikpKSArICgoKHN5KSAqICh1cF96KSkpKSkpKSk7CiAgICAgICAgICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfNyA9IG5vcm1hbGl6ZShyeCwgcnksIHJ6KTsKICAgICAgICAgICAgbGV0IGR4ID0gX19weXRyYV90dXBsZV83WzBdOwogICAgICAgICAgICBsZXQgZHkgPSBfX3B5dHJhX3R1cGxlXzdbMV07CiAgICAgICAgICAgIGxldCBkeiA9IF9fcHl0cmFfdHVwbGVfN1syXTsKICAgICAgICAgICAgbGV0IGJlc3RfdCA9IDEwMDAwMDAwMDAuMDsKICAgICAgICAgICAgbGV0IGhpdF9raW5kID0gMDsKICAgICAgICAgICAgbGV0IHIgPSAwLjA7CiAgICAgICAgICAgIGxldCBnID0gMC4wOwogICAgICAgICAgICBsZXQgYiA9IDAuMDsKICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGR5KSA8ICgoLSgxZS0wNikpKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgdGYgPSAoKCgoKC0oMS4yKSkpIC0gKGNhbV95KSkpIC8gKGR5KSk7CiAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoKHRmKSA+ICgwLjAwMDEpKSAmJiAoKHRmKSA8IChiZXN0X3QpKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYmVzdF90ID0gdGY7CiAgICAgICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAxOwogICAgICAgICAgICAgICAgfQogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MCA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczB4LCBzMHksIHMweiwgMC42NSk7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDApID4gKDAuMCkpICYmICgodDApIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQwOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAyOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MSA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczF4LCBzMXksIHMxeiwgMC43Mik7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDEpID4gKDAuMCkpICYmICgodDEpIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQxOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAzOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MiA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczJ4LCBzMnksIHMyeiwgMC41OCk7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDIpID4gKDAuMCkpICYmICgodDIpIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQyOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSA0OwogICAgICAgICAgICB9CiAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgwKSkpKSB7CiAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzggPSBza3lfY29sb3IoZHgsIGR5LCBkeiwgdHBoYXNlKTsKICAgICAgICAgICAgICAgIHIgPSBfX3B5dHJhX3R1cGxlXzhbMF07CiAgICAgICAgICAgICAgICBnID0gX19weXRyYV90dXBsZV84WzFdOwogICAgICAgICAgICAgICAgYiA9IF9fcHl0cmFfdHVwbGVfOFsyXTsKICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgxKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgbGV0IGh4ID0gKChjYW1feCkgKyAoKChiZXN0X3QpICogKGR4KSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgaHogPSAoKGNhbV96KSArICgoKGJlc3RfdCkgKiAoZHopKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBjeCA9IE1hdGgudHJ1bmMoTnVtYmVyKG1hdGguZmxvb3IoKChoeCkgKiAoMi4wKSkpKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGN6ID0gTWF0aC50cnVuYyhOdW1iZXIobWF0aC5mbG9vcigoKGh6KSAqICgyLjApKSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgY2hlY2tlciA9IChweUJvb2woKChweU1vZCgoKGN4KSArIChjeikpLCAyKSkgPT09ICgwKSkpID8gMCA6IDEpOwogICAgICAgICAgICAgICAgICAgIGxldCBiYXNlX3IgPSAocHlCb29sKCgoY2hlY2tlcikgPT09ICgwKSkpID8gMC4xIDogMC4wNCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGJhc2VfZyA9IChweUJvb2woKChjaGVja2VyKSA9PT0gKDApKSkgPyAwLjExIDogMC4wNSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGJhc2VfYiA9IChweUJvb2woKChjaGVja2VyKSA9PT0gKDApKSkgPyAwLjEzIDogMC4wOCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx4diA9ICgobHgpIC0gKGh4KSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx5diA9ICgobHkpIC0gKCgtKDEuMikpKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx6diA9ICgobHopIC0gKGh6KSk7CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV85ID0gbm9ybWFsaXplKGx4diwgbHl2LCBsenYpOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHggPSBfX3B5dHJhX3R1cGxlXzlbMF07CiAgICAgICAgICAgICAgICAgICAgbGV0IGxkeSA9IF9fcHl0cmFfdHVwbGVfOVsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgbGR6ID0gX19weXRyYV90dXBsZV85WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90bCA9IE1hdGgubWF4KGxkeSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbGRpc3QyID0gKCgoKCgobHh2KSAqIChseHYpKSkgKyAoKChseXYpICogKGx5dikpKSkpICsgKCgobHp2KSAqIChsenYpKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBnbG93ID0gKCg4LjApIC8gKCgoMS4wKSArIChsZGlzdDIpKSkpOwogICAgICAgICAgICAgICAgICAgIHIgPSAoKCgoYmFzZV9yKSArICgoKDAuOCkgKiAoZ2xvdykpKSkpICsgKCgoMC4yKSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9ICgoKChiYXNlX2cpICsgKCgoMC41KSAqIChnbG93KSkpKSkgKyAoKCgwLjE4KSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICAgICAgYiA9ICgoKChiYXNlX2IpICsgKCgoMS4wKSAqIChnbG93KSkpKSkgKyAoKCgwLjI0KSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICB9IGVsc2UgewogICAgICAgICAgICAgICAgICAgIGxldCBjeCA9IDAuMDsKICAgICAgICAgICAgICAgICAgICBsZXQgY3kgPSAwLjA7CiAgICAgICAgICAgICAgICAgICAgbGV0IGN6ID0gMC4wOwogICAgICAgICAgICAgICAgICAgIGxldCByYWQgPSAxLjA7CiAgICAgICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGhpdF9raW5kKSA9PT0gKDIpKSkpIHsKICAgICAgICAgICAgICAgICAgICAgICAgY3ggPSBzMHg7CiAgICAgICAgICAgICAgICAgICAgICAgIGN5ID0gczB5OwogICAgICAgICAgICAgICAgICAgICAgICBjeiA9IHMwejsKICAgICAgICAgICAgICAgICAgICAgICAgcmFkID0gMC42NTsKICAgICAgICAgICAgICAgICAgICB9IGVsc2UgewogICAgICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoaGl0X2tpbmQpID09PSAoMykpKSkgewogICAgICAgICAgICAgICAgICAgICAgICAgICAgY3ggPSBzMXg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjeSA9IHMxeTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGN6ID0gczF6OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgcmFkID0gMC43MjsKICAgICAgICAgICAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGN4ID0gczJ4OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgY3kgPSBzMnk7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjeiA9IHMyejsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHJhZCA9IDAuNTg7CiAgICAgICAgICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICAgICAgbGV0IGh4ID0gKChjYW1feCkgKyAoKChiZXN0X3QpICogKGR4KSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgaHkgPSAoKGNhbV95KSArICgoKGJlc3RfdCkgKiAoZHkpKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBoeiA9ICgoY2FtX3opICsgKCgoYmVzdF90KSAqIChkeikpKSk7CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV8xMCA9IG5vcm1hbGl6ZSgoKCgoaHgpIC0gKGN4KSkpIC8gKHJhZCkpLCAoKCgoaHkpIC0gKGN5KSkpIC8gKHJhZCkpLCAoKCgoaHopIC0gKGN6KSkpIC8gKHJhZCkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbnggPSBfX3B5dHJhX3R1cGxlXzEwWzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBueSA9IF9fcHl0cmFfdHVwbGVfMTBbMV07CiAgICAgICAgICAgICAgICAgICAgbGV0IG56ID0gX19weXRyYV90dXBsZV8xMFsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzExID0gcmVmbGVjdChkeCwgZHksIGR6LCBueCwgbnksIG56KTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR4ID0gX19weXRyYV90dXBsZV8xMVswXTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR5ID0gX19weXRyYV90dXBsZV8xMVsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR6ID0gX19weXRyYV90dXBsZV8xMVsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzEyID0gcmVmcmFjdChkeCwgZHksIGR6LCBueCwgbnksIG56LCAoKDEuMCkgLyAoMS40NSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR4ID0gX19weXRyYV90dXBsZV8xMlswXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR5ID0gX19weXRyYV90dXBsZV8xMlsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR6ID0gX19weXRyYV90dXBsZV8xMlsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzEzID0gc2t5X2NvbG9yKHJkeCwgcmR5LCByZHosIHRwaGFzZSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IHNyID0gX19weXRyYV90dXBsZV8xM1swXTsKICAgICAgICAgICAgICAgICAgICBsZXQgc2cgPSBfX3B5dHJhX3R1cGxlXzEzWzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBzYiA9IF9fcHl0cmFfdHVwbGVfMTNbMl07CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV8xNCA9IHNreV9jb2xvcih0ZHgsIHRkeSwgdGR6LCAoKHRwaGFzZSkgKyAoMC44KSkpOwogICAgICAgICAgICAgICAgICAgIGxldCB0ciA9IF9fcHl0cmFfdHVwbGVfMTRbMF07CiAgICAgICAgICAgICAgICAgICAgbGV0IHRnID0gX19weXRyYV90dXBsZV8xNFsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGIgPSBfX3B5dHJhX3R1cGxlXzE0WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBjb3NpID0gTWF0aC5tYXgoKC0oKCgoKCgoZHgpICogKG54KSkpICsgKCgoZHkpICogKG55KSkpKSkgKyAoKChkeikgKiAobnopKSkpKSksIDAuMCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGZyID0gc2NobGljayhjb3NpLCAwLjA0KTsKICAgICAgICAgICAgICAgICAgICByID0gKCgoKHRyKSAqICgoKDEuMCkgLSAoZnIpKSkpKSArICgoKHNyKSAqIChmcikpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9ICgoKCh0ZykgKiAoKCgxLjApIC0gKGZyKSkpKSkgKyAoKChzZykgKiAoZnIpKSkpOwogICAgICAgICAgICAgICAgICAgIGIgPSAoKCgodGIpICogKCgoMS4wKSAtIChmcikpKSkpICsgKCgoc2IpICogKGZyKSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHh2ID0gKChseCkgLSAoaHgpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHl2ID0gKChseSkgLSAoaHkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHp2ID0gKChseikgLSAoaHopKTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzE1ID0gbm9ybWFsaXplKGx4diwgbHl2LCBsenYpOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHggPSBfX3B5dHJhX3R1cGxlXzE1WzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHkgPSBfX3B5dHJhX3R1cGxlXzE1WzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHogPSBfX3B5dHJhX3R1cGxlXzE1WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90bCA9IE1hdGgubWF4KCgoKCgoKG54KSAqIChsZHgpKSkgKyAoKChueSkgKiAobGR5KSkpKSkgKyAoKChueikgKiAobGR6KSkpKSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzE2ID0gbm9ybWFsaXplKCgobGR4KSAtIChkeCkpLCAoKGxkeSkgLSAoZHkpKSwgKChsZHopIC0gKGR6KSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBodnggPSBfX3B5dHJhX3R1cGxlXzE2WzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBodnkgPSBfX3B5dHJhX3R1cGxlXzE2WzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBodnogPSBfX3B5dHJhX3R1cGxlXzE2WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90aCA9IE1hdGgubWF4KCgoKCgoKG54KSAqIChodngpKSkgKyAoKChueSkgKiAoaHZ5KSkpKSkgKyAoKChueikgKiAoaHZ6KSkpKSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBsZXQgc3BlYyA9ICgobmRvdGgpICogKG5kb3RoKSk7CiAgICAgICAgICAgICAgICAgICAgc3BlYyA9ICgoc3BlYykgKiAoc3BlYykpOwogICAgICAgICAgICAgICAgICAgIHNwZWMgPSAoKHNwZWMpICogKHNwZWMpKTsKICAgICAgICAgICAgICAgICAgICBzcGVjID0gKChzcGVjKSAqIChzcGVjKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGdsb3cgPSAoKDEwLjApIC8gKCgoKCgoKDEuMCkgKyAoKChseHYpICogKGx4dikpKSkpICsgKCgobHl2KSAqIChseXYpKSkpKSArICgoKGx6dikgKiAobHp2KSkpKSkpOwogICAgICAgICAgICAgICAgICAgIHIgPSByICsgKCgoKCgoMC4yKSAqIChuZG90bCkpKSArICgoKDAuOCkgKiAoc3BlYykpKSkpICsgKCgoMC40NSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9IGcgKyAoKCgoKCgwLjE4KSAqIChuZG90bCkpKSArICgoKDAuNikgKiAoc3BlYykpKSkpICsgKCgoMC4zNSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgYiA9IGIgKyAoKCgoKCgwLjI2KSAqIChuZG90bCkpKSArICgoKDEuMCkgKiAoc3BlYykpKSkpICsgKCgoMC42NSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGhpdF9raW5kKSA9PT0gKDIpKSkpIHsKICAgICAgICAgICAgICAgICAgICAgICAgciA9IHIgKiAwLjk1OwogICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDEuMDU7CiAgICAgICAgICAgICAgICAgICAgICAgIGIgPSBiICogMS4xOwogICAgICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgzKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICByID0gciAqIDEuMDg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDAuOTg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBiID0gYiAqIDEuMDQ7CiAgICAgICAgICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICByID0gciAqIDEuMDI7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDEuMTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGIgPSBiICogMC45NTsKICAgICAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgfQogICAgICAgICAgICByID0gbWF0aC5zcXJ0KGNsYW1wMDEocikpOwogICAgICAgICAgICBnID0gbWF0aC5zcXJ0KGNsYW1wMDEoZykpOwogICAgICAgICAgICBiID0gbWF0aC5zcXJ0KGNsYW1wMDEoYikpOwogICAgICAgICAgICBmcmFtZVtpXSA9IHF1YW50aXplXzMzMihyLCBnLCBiKTsKICAgICAgICAgICAgaSA9IGkgKyAxOwogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zKCkgewogICAgbGV0IHdpZHRoID0gMzIwOwogICAgbGV0IGhlaWdodCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDcyOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzE3ID0gMDsgX19weXRyYV9pXzE3IDwgZnJhbWVzX247IF9fcHl0cmFfaV8xNyArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV8xNzsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgaSwgZnJhbWVzX24pKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBmcmFtZXMsIHBhbGV0dGVfMzMyKCksIDYsIDApOwogICAgbGV0IGVsYXBzZWQgPSAoKHBlcmZfY291bnRlcigpKSAtIChzdGFydCkpOwogICAgcHlQcmludCgnb3V0cHV0OicsIG91dF9wYXRoKTsKICAgIHB5UHJpbnQoJ2ZyYW1lczonLCBmcmFtZXNfbik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zKCk7Cg=="
let pytraArgs = Array(CommandLine.arguments.dropFirst())
let pytraCode = pytraRunEmbeddedNode(pytraEmbeddedJsBase64, pytraArgs)
Foundation.exit(pytraCode)
```
</details>

<details>
<summary>Kotlinへの変換例 : 16_glass_sculpture_chaos.kt</summary>

```kotlin
// このファイルは自動生成です（Python -> Kotlin node-backed mode）。

// Kotlin 実行向け Node.js ランタイム補助。

import java.io.File
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import java.util.UUID

/**
 * Base64 で埋め込まれた JavaScript ソースコードを一時ファイルへ展開し、node で実行する。
 */
object PyRuntime {
    /**
     * @param sourceBase64 JavaScript ソースコードの Base64 文字列。
     * @param args JavaScript 側へ渡す引数配列。
     * @return node プロセスの終了コード。失敗時は 1 を返す。
     */
    @JvmStatic
    fun runEmbeddedNode(sourceBase64: String, args: Array<String>): Int {
        val sourceBytes: ByteArray = try {
            Base64.getDecoder().decode(sourceBase64)
        } catch (ex: IllegalArgumentException) {
            System.err.println("error: failed to decode embedded JavaScript source")
            return 1
        }

        val tempFile: Path = try {
            val name = "pytra_embedded_${UUID.randomUUID()}.js"
            val p = File(System.getProperty("java.io.tmpdir"), name).toPath()
            Files.write(p, sourceBytes)
            p
        } catch (ex: Exception) {
            System.err.println("error: failed to write temporary JavaScript file: ${ex.message}")
            return 1
        }

        val command = mutableListOf("node", tempFile.toString())
        command.addAll(args)
        val process: Process = try {
            ProcessBuilder(command)
                .inheritIO()
                .start()
        } catch (ex: Exception) {
            System.err.println("error: failed to launch node: ${ex.message}")
            try {
                Files.deleteIfExists(tempFile)
            } catch (_: Exception) {
            }
            return 1
        }

        val code = process.waitFor()
        try {
            Files.deleteIfExists(tempFile)
        } catch (_: Exception) {
        }
        return code
    }
}

class pytra_16_glass_sculpture_chaos {
    companion object {
        // 埋め込み JavaScript ソース（Base64）。
        private const val PYTRA_EMBEDDED_JS_BASE64: String = "Ly8gZ2VuZXJhdGVkIGludGVybmFsIEphdmFTY3JpcHQKCmNvbnN0IF9fcHl0cmFfcm9vdCA9IHByb2Nlc3MuY3dkKCk7CmNvbnN0IHB5X3J1bnRpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9weV9ydW50aW1lLmpzJyk7CmNvbnN0IHB5X21hdGggPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS9tYXRoLmpzJyk7CmNvbnN0IHB5X3RpbWUgPSByZXF1aXJlKF9fcHl0cmFfcm9vdCArICcvc3JjL2pzX21vZHVsZS90aW1lLmpzJyk7CmNvbnN0IHsgcHlQcmludCwgcHlMZW4sIHB5Qm9vbCwgcHlSYW5nZSwgcHlGbG9vckRpdiwgcHlNb2QsIHB5SW4sIHB5U2xpY2UsIHB5T3JkLCBweUNociwgcHlCeXRlYXJyYXksIHB5Qnl0ZXMsIHB5SXNEaWdpdCwgcHlJc0FscGhhIH0gPSBweV9ydW50aW1lOwpjb25zdCB7IHBlcmZDb3VudGVyIH0gPSBweV90aW1lOwpjb25zdCBtYXRoID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvbWF0aC5qcycpOwpjb25zdCBwZXJmX2NvdW50ZXIgPSBwZXJmQ291bnRlcjsKY29uc3QgeyBzYXZlX2dpZiB9ID0gcmVxdWlyZShfX3B5dHJhX3Jvb3QgKyAnL3NyYy9qc19tb2R1bGUvZ2lmX2hlbHBlci5qcycpOwoKZnVuY3Rpb24gY2xhbXAwMSh2KSB7CiAgICBpZiAocHlCb29sKCgodikgPCAoMC4wKSkpKSB7CiAgICAgICAgcmV0dXJuIDAuMDsKICAgIH0KICAgIGlmIChweUJvb2woKCh2KSA+ICgxLjApKSkpIHsKICAgICAgICByZXR1cm4gMS4wOwogICAgfQogICAgcmV0dXJuIHY7Cn0KZnVuY3Rpb24gZG90KGF4LCBheSwgYXosIGJ4LCBieSwgYnopIHsKICAgIHJldHVybiAoKCgoKChheCkgKiAoYngpKSkgKyAoKChheSkgKiAoYnkpKSkpKSArICgoKGF6KSAqIChieikpKSk7Cn0KZnVuY3Rpb24gbGVuZ3RoKHgsIHksIHopIHsKICAgIHJldHVybiBtYXRoLnNxcnQoKCgoKCgoeCkgKiAoeCkpKSArICgoKHkpICogKHkpKSkpKSArICgoKHopICogKHopKSkpKTsKfQpmdW5jdGlvbiBub3JtYWxpemUoeCwgeSwgeikgewogICAgbGV0IGwgPSBsZW5ndGgoeCwgeSwgeik7CiAgICBpZiAocHlCb29sKCgobCkgPCAoMWUtMDkpKSkpIHsKICAgICAgICByZXR1cm4gWzAuMCwgMC4wLCAwLjBdOwogICAgfQogICAgcmV0dXJuIFsoKHgpIC8gKGwpKSwgKCh5KSAvIChsKSksICgoeikgLyAobCkpXTsKfQpmdW5jdGlvbiByZWZsZWN0KGl4LCBpeSwgaXosIG54LCBueSwgbnopIHsKICAgIGxldCBkID0gKChkb3QoaXgsIGl5LCBpeiwgbngsIG55LCBueikpICogKDIuMCkpOwogICAgcmV0dXJuIFsoKGl4KSAtICgoKGQpICogKG54KSkpKSwgKChpeSkgLSAoKChkKSAqIChueSkpKSksICgoaXopIC0gKCgoZCkgKiAobnopKSkpXTsKfQpmdW5jdGlvbiByZWZyYWN0KGl4LCBpeSwgaXosIG54LCBueSwgbnosIGV0YSkgewogICAgbGV0IGNvc2kgPSAoLShkb3QoaXgsIGl5LCBpeiwgbngsIG55LCBueikpKTsKICAgIGxldCBzaW50MiA9ICgoKChldGEpICogKGV0YSkpKSAqICgoKDEuMCkgLSAoKChjb3NpKSAqIChjb3NpKSkpKSkpOwogICAgaWYgKHB5Qm9vbCgoKHNpbnQyKSA+ICgxLjApKSkpIHsKICAgICAgICByZXR1cm4gcmVmbGVjdChpeCwgaXksIGl6LCBueCwgbnksIG56KTsKICAgIH0KICAgIGxldCBjb3N0ID0gbWF0aC5zcXJ0KCgoMS4wKSAtIChzaW50MikpKTsKICAgIGxldCBrID0gKCgoKGV0YSkgKiAoY29zaSkpKSAtIChjb3N0KSk7CiAgICByZXR1cm4gWygoKChldGEpICogKGl4KSkpICsgKCgoaykgKiAobngpKSkpLCAoKCgoZXRhKSAqIChpeSkpKSArICgoKGspICogKG55KSkpKSwgKCgoKGV0YSkgKiAoaXopKSkgKyAoKChrKSAqIChueikpKSldOwp9CmZ1bmN0aW9uIHNjaGxpY2soY29zX3RoZXRhLCBmMCkgewogICAgbGV0IG0gPSAoKDEuMCkgLSAoY29zX3RoZXRhKSk7CiAgICByZXR1cm4gKChmMCkgKyAoKCgoKDEuMCkgLSAoZjApKSkgKiAoKCgoKCgoKChtKSAqIChtKSkpICogKG0pKSkgKiAobSkpKSAqIChtKSkpKSkpOwp9CmZ1bmN0aW9uIHNreV9jb2xvcihkeCwgZHksIGR6LCB0cGhhc2UpIHsKICAgIGxldCB0ID0gKCgwLjUpICogKCgoZHkpICsgKDEuMCkpKSk7CiAgICBsZXQgciA9ICgoMC4wNikgKyAoKCgwLjIpICogKHQpKSkpOwogICAgbGV0IGcgPSAoKDAuMSkgKyAoKCgwLjI1KSAqICh0KSkpKTsKICAgIGxldCBiID0gKCgwLjE2KSArICgoKDAuNDUpICogKHQpKSkpOwogICAgbGV0IGJhbmQgPSAoKDAuNSkgKyAoKCgwLjUpICogKG1hdGguc2luKCgoKCgoKDguMCkgKiAoZHgpKSkgKyAoKCg2LjApICogKGR6KSkpKSkgKyAodHBoYXNlKSkpKSkpKTsKICAgIHIgPSByICsgKCgwLjA4KSAqIChiYW5kKSk7CiAgICBnID0gZyArICgoMC4wNSkgKiAoYmFuZCkpOwogICAgYiA9IGIgKyAoKDAuMTIpICogKGJhbmQpKTsKICAgIHJldHVybiBbY2xhbXAwMShyKSwgY2xhbXAwMShnKSwgY2xhbXAwMShiKV07Cn0KZnVuY3Rpb24gc3BoZXJlX2ludGVyc2VjdChveCwgb3ksIG96LCBkeCwgZHksIGR6LCBjeCwgY3ksIGN6LCByYWRpdXMpIHsKICAgIGxldCBseCA9ICgob3gpIC0gKGN4KSk7CiAgICBsZXQgbHkgPSAoKG95KSAtIChjeSkpOwogICAgbGV0IGx6ID0gKChveikgLSAoY3opKTsKICAgIGxldCBiID0gKCgoKCgobHgpICogKGR4KSkpICsgKCgobHkpICogKGR5KSkpKSkgKyAoKChseikgKiAoZHopKSkpOwogICAgbGV0IGMgPSAoKCgoKCgoKGx4KSAqIChseCkpKSArICgoKGx5KSAqIChseSkpKSkpICsgKCgobHopICogKGx6KSkpKSkgLSAoKChyYWRpdXMpICogKHJhZGl1cykpKSk7CiAgICBsZXQgaCA9ICgoKChiKSAqIChiKSkpIC0gKGMpKTsKICAgIGlmIChweUJvb2woKChoKSA8ICgwLjApKSkpIHsKICAgICAgICByZXR1cm4gKC0oMS4wKSk7CiAgICB9CiAgICBsZXQgcyA9IG1hdGguc3FydChoKTsKICAgIGxldCB0MCA9ICgoKC0oYikpKSAtIChzKSk7CiAgICBpZiAocHlCb29sKCgodDApID4gKDAuMDAwMSkpKSkgewogICAgICAgIHJldHVybiB0MDsKICAgIH0KICAgIGxldCB0MSA9ICgoKC0oYikpKSArIChzKSk7CiAgICBpZiAocHlCb29sKCgodDEpID4gKDAuMDAwMSkpKSkgewogICAgICAgIHJldHVybiB0MTsKICAgIH0KICAgIHJldHVybiAoLSgxLjApKTsKfQpmdW5jdGlvbiBwYWxldHRlXzMzMigpIHsKICAgIGxldCBwID0gcHlCeXRlYXJyYXkoKCgyNTYpICogKDMpKSk7CiAgICBsZXQgaTsKICAgIGZvciAobGV0IF9fcHl0cmFfaV8xID0gMDsgX19weXRyYV9pXzEgPCAyNTY7IF9fcHl0cmFfaV8xICs9IDEpIHsKICAgICAgICBpID0gX19weXRyYV9pXzE7CiAgICAgICAgbGV0IHIgPSAoKCgoaSkgPj4gKDUpKSkgJiAoNykpOwogICAgICAgIGxldCBnID0gKCgoKGkpID4+ICgyKSkpICYgKDcpKTsKICAgICAgICBsZXQgYiA9ICgoaSkgJiAoMykpOwogICAgICAgIHBbKCgoKGkpICogKDMpKSkgKyAoMCkpXSA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoKCgyNTUpICogKHIpKSkgLyAoNykpKSk7CiAgICAgICAgcFsoKCgoaSkgKiAoMykpKSArICgxKSldID0gTWF0aC50cnVuYyhOdW1iZXIoKCgoKDI1NSkgKiAoZykpKSAvICg3KSkpKTsKICAgICAgICBwWygoKChpKSAqICgzKSkpICsgKDIpKV0gPSBNYXRoLnRydW5jKE51bWJlcigoKCgoMjU1KSAqIChiKSkpIC8gKDMpKSkpOwogICAgfQogICAgcmV0dXJuIHB5Qnl0ZXMocCk7Cn0KZnVuY3Rpb24gcXVhbnRpemVfMzMyKHIsIGcsIGIpIHsKICAgIGxldCByciA9IE1hdGgudHJ1bmMoTnVtYmVyKCgoY2xhbXAwMShyKSkgKiAoMjU1LjApKSkpOwogICAgbGV0IGdnID0gTWF0aC50cnVuYyhOdW1iZXIoKChjbGFtcDAxKGcpKSAqICgyNTUuMCkpKSk7CiAgICBsZXQgYmIgPSBNYXRoLnRydW5jKE51bWJlcigoKGNsYW1wMDEoYikpICogKDI1NS4wKSkpKTsKICAgIHJldHVybiAoKCgoKCgoKHJyKSA+PiAoNSkpKSA8PCAoNSkpKSArICgoKCgoZ2cpID4+ICg1KSkpIDw8ICgyKSkpKSkgKyAoKChiYikgPj4gKDYpKSkpOwp9CmZ1bmN0aW9uIHJlbmRlcl9mcmFtZSh3aWR0aCwgaGVpZ2h0LCBmcmFtZV9pZCwgZnJhbWVzX24pIHsKICAgIGxldCB0ID0gKChmcmFtZV9pZCkgLyAoZnJhbWVzX24pKTsKICAgIGxldCB0cGhhc2UgPSAoKCgoMi4wKSAqIChtYXRoLnBpKSkpICogKHQpKTsKICAgIGxldCBjYW1fciA9IDMuMDsKICAgIGxldCBjYW1feCA9ICgoY2FtX3IpICogKG1hdGguY29zKCgodHBoYXNlKSAqICgwLjkpKSkpKTsKICAgIGxldCBjYW1feSA9ICgoMS4xKSArICgoKDAuMjUpICogKG1hdGguc2luKCgodHBoYXNlKSAqICgwLjYpKSkpKSkpOwogICAgbGV0IGNhbV96ID0gKChjYW1fcikgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDAuOSkpKSkpOwogICAgbGV0IGxvb2tfeCA9IDAuMDsKICAgIGxldCBsb29rX3kgPSAwLjM1OwogICAgbGV0IGxvb2tfeiA9IDAuMDsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfMiA9IG5vcm1hbGl6ZSgoKGxvb2tfeCkgLSAoY2FtX3gpKSwgKChsb29rX3kpIC0gKGNhbV95KSksICgobG9va196KSAtIChjYW1feikpKTsKICAgIGxldCBmd2RfeCA9IF9fcHl0cmFfdHVwbGVfMlswXTsKICAgIGxldCBmd2RfeSA9IF9fcHl0cmFfdHVwbGVfMlsxXTsKICAgIGxldCBmd2RfeiA9IF9fcHl0cmFfdHVwbGVfMlsyXTsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfMyA9IG5vcm1hbGl6ZShmd2RfeiwgMC4wLCAoLShmd2RfeCkpKTsKICAgIGxldCByaWdodF94ID0gX19weXRyYV90dXBsZV8zWzBdOwogICAgbGV0IHJpZ2h0X3kgPSBfX3B5dHJhX3R1cGxlXzNbMV07CiAgICBsZXQgcmlnaHRfeiA9IF9fcHl0cmFfdHVwbGVfM1syXTsKICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfNCA9IG5vcm1hbGl6ZSgoKCgocmlnaHRfeSkgKiAoZndkX3opKSkgLSAoKChyaWdodF96KSAqIChmd2RfeSkpKSksICgoKChyaWdodF96KSAqIChmd2RfeCkpKSAtICgoKHJpZ2h0X3gpICogKGZ3ZF96KSkpKSwgKCgoKHJpZ2h0X3gpICogKGZ3ZF95KSkpIC0gKCgocmlnaHRfeSkgKiAoZndkX3gpKSkpKTsKICAgIGxldCB1cF94ID0gX19weXRyYV90dXBsZV80WzBdOwogICAgbGV0IHVwX3kgPSBfX3B5dHJhX3R1cGxlXzRbMV07CiAgICBsZXQgdXBfeiA9IF9fcHl0cmFfdHVwbGVfNFsyXTsKICAgIGxldCBzMHggPSAoKDAuOSkgKiAobWF0aC5jb3MoKCgxLjMpICogKHRwaGFzZSkpKSkpOwogICAgbGV0IHMweSA9ICgoMC4xNSkgKyAoKCgwLjM1KSAqIChtYXRoLnNpbigoKDEuNykgKiAodHBoYXNlKSkpKSkpKTsKICAgIGxldCBzMHogPSAoKDAuOSkgKiAobWF0aC5zaW4oKCgxLjMpICogKHRwaGFzZSkpKSkpOwogICAgbGV0IHMxeCA9ICgoMS4yKSAqIChtYXRoLmNvcygoKCgoMS4zKSAqICh0cGhhc2UpKSkgKyAoMi4wOTQpKSkpKTsKICAgIGxldCBzMXkgPSAoKDAuMSkgKyAoKCgwLjQpICogKG1hdGguc2luKCgoKCgxLjEpICogKHRwaGFzZSkpKSArICgwLjgpKSkpKSkpOwogICAgbGV0IHMxeiA9ICgoMS4yKSAqIChtYXRoLnNpbigoKCgoMS4zKSAqICh0cGhhc2UpKSkgKyAoMi4wOTQpKSkpKTsKICAgIGxldCBzMnggPSAoKDEuMCkgKiAobWF0aC5jb3MoKCgoKDEuMykgKiAodHBoYXNlKSkpICsgKDQuMTg4KSkpKSk7CiAgICBsZXQgczJ5ID0gKCgwLjIpICsgKCgoMC4zKSAqIChtYXRoLnNpbigoKCgoMS41KSAqICh0cGhhc2UpKSkgKyAoMS45KSkpKSkpKTsKICAgIGxldCBzMnogPSAoKDEuMCkgKiAobWF0aC5zaW4oKCgoKDEuMykgKiAodHBoYXNlKSkpICsgKDQuMTg4KSkpKSk7CiAgICBsZXQgbHIgPSAwLjM1OwogICAgbGV0IGx4ID0gKCgyLjQpICogKG1hdGguY29zKCgodHBoYXNlKSAqICgxLjgpKSkpKTsKICAgIGxldCBseSA9ICgoMS44KSArICgoKDAuOCkgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDEuMikpKSkpKSk7CiAgICBsZXQgbHogPSAoKDIuNCkgKiAobWF0aC5zaW4oKCh0cGhhc2UpICogKDEuOCkpKSkpOwogICAgbGV0IGZyYW1lID0gcHlCeXRlYXJyYXkoKCh3aWR0aCkgKiAoaGVpZ2h0KSkpOwogICAgbGV0IGFzcGVjdCA9ICgod2lkdGgpIC8gKGhlaWdodCkpOwogICAgbGV0IGZvdiA9IDEuMjU7CiAgICBsZXQgaSA9IDA7CiAgICBsZXQgcHk7CiAgICBmb3IgKGxldCBfX3B5dHJhX2lfNSA9IDA7IF9fcHl0cmFfaV81IDwgaGVpZ2h0OyBfX3B5dHJhX2lfNSArPSAxKSB7CiAgICAgICAgcHkgPSBfX3B5dHJhX2lfNTsKICAgICAgICBsZXQgc3kgPSAoKDEuMCkgLSAoKCgoKDIuMCkgKiAoKChweSkgKyAoMC41KSkpKSkgLyAoaGVpZ2h0KSkpKTsKICAgICAgICBsZXQgcHg7CiAgICAgICAgZm9yIChsZXQgX19weXRyYV9pXzYgPSAwOyBfX3B5dHJhX2lfNiA8IHdpZHRoOyBfX3B5dHJhX2lfNiArPSAxKSB7CiAgICAgICAgICAgIHB4ID0gX19weXRyYV9pXzY7CiAgICAgICAgICAgIGxldCBzeCA9ICgoKCgoKCgoMi4wKSAqICgoKHB4KSArICgwLjUpKSkpKSAvICh3aWR0aCkpKSAtICgxLjApKSkgKiAoYXNwZWN0KSk7CiAgICAgICAgICAgIGxldCByeCA9ICgoZndkX3gpICsgKCgoZm92KSAqICgoKCgoc3gpICogKHJpZ2h0X3gpKSkgKyAoKChzeSkgKiAodXBfeCkpKSkpKSkpOwogICAgICAgICAgICBsZXQgcnkgPSAoKGZ3ZF95KSArICgoKGZvdikgKiAoKCgoKHN4KSAqIChyaWdodF95KSkpICsgKCgoc3kpICogKHVwX3kpKSkpKSkpKTsKICAgICAgICAgICAgbGV0IHJ6ID0gKChmd2RfeikgKyAoKChmb3YpICogKCgoKChzeCkgKiAocmlnaHRfeikpKSArICgoKHN5KSAqICh1cF96KSkpKSkpKSk7CiAgICAgICAgICAgIGNvbnN0IF9fcHl0cmFfdHVwbGVfNyA9IG5vcm1hbGl6ZShyeCwgcnksIHJ6KTsKICAgICAgICAgICAgbGV0IGR4ID0gX19weXRyYV90dXBsZV83WzBdOwogICAgICAgICAgICBsZXQgZHkgPSBfX3B5dHJhX3R1cGxlXzdbMV07CiAgICAgICAgICAgIGxldCBkeiA9IF9fcHl0cmFfdHVwbGVfN1syXTsKICAgICAgICAgICAgbGV0IGJlc3RfdCA9IDEwMDAwMDAwMDAuMDsKICAgICAgICAgICAgbGV0IGhpdF9raW5kID0gMDsKICAgICAgICAgICAgbGV0IHIgPSAwLjA7CiAgICAgICAgICAgIGxldCBnID0gMC4wOwogICAgICAgICAgICBsZXQgYiA9IDAuMDsKICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGR5KSA8ICgoLSgxZS0wNikpKSkpKSB7CiAgICAgICAgICAgICAgICBsZXQgdGYgPSAoKCgoKC0oMS4yKSkpIC0gKGNhbV95KSkpIC8gKGR5KSk7CiAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoKHRmKSA+ICgwLjAwMDEpKSAmJiAoKHRmKSA8IChiZXN0X3QpKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgYmVzdF90ID0gdGY7CiAgICAgICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAxOwogICAgICAgICAgICAgICAgfQogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MCA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczB4LCBzMHksIHMweiwgMC42NSk7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDApID4gKDAuMCkpICYmICgodDApIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQwOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAyOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MSA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczF4LCBzMXksIHMxeiwgMC43Mik7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDEpID4gKDAuMCkpICYmICgodDEpIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQxOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSAzOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGxldCB0MiA9IHNwaGVyZV9pbnRlcnNlY3QoY2FtX3gsIGNhbV95LCBjYW1feiwgZHgsIGR5LCBkeiwgczJ4LCBzMnksIHMyeiwgMC41OCk7CiAgICAgICAgICAgIGlmIChweUJvb2woKCgodDIpID4gKDAuMCkpICYmICgodDIpIDwgKGJlc3RfdCkpKSkpIHsKICAgICAgICAgICAgICAgIGJlc3RfdCA9IHQyOwogICAgICAgICAgICAgICAgaGl0X2tpbmQgPSA0OwogICAgICAgICAgICB9CiAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgwKSkpKSB7CiAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzggPSBza3lfY29sb3IoZHgsIGR5LCBkeiwgdHBoYXNlKTsKICAgICAgICAgICAgICAgIHIgPSBfX3B5dHJhX3R1cGxlXzhbMF07CiAgICAgICAgICAgICAgICBnID0gX19weXRyYV90dXBsZV84WzFdOwogICAgICAgICAgICAgICAgYiA9IF9fcHl0cmFfdHVwbGVfOFsyXTsKICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgxKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgbGV0IGh4ID0gKChjYW1feCkgKyAoKChiZXN0X3QpICogKGR4KSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgaHogPSAoKGNhbV96KSArICgoKGJlc3RfdCkgKiAoZHopKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBjeCA9IE1hdGgudHJ1bmMoTnVtYmVyKG1hdGguZmxvb3IoKChoeCkgKiAoMi4wKSkpKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGN6ID0gTWF0aC50cnVuYyhOdW1iZXIobWF0aC5mbG9vcigoKGh6KSAqICgyLjApKSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgY2hlY2tlciA9IChweUJvb2woKChweU1vZCgoKGN4KSArIChjeikpLCAyKSkgPT09ICgwKSkpID8gMCA6IDEpOwogICAgICAgICAgICAgICAgICAgIGxldCBiYXNlX3IgPSAocHlCb29sKCgoY2hlY2tlcikgPT09ICgwKSkpID8gMC4xIDogMC4wNCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGJhc2VfZyA9IChweUJvb2woKChjaGVja2VyKSA9PT0gKDApKSkgPyAwLjExIDogMC4wNSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGJhc2VfYiA9IChweUJvb2woKChjaGVja2VyKSA9PT0gKDApKSkgPyAwLjEzIDogMC4wOCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx4diA9ICgobHgpIC0gKGh4KSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx5diA9ICgobHkpIC0gKCgtKDEuMikpKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGx6diA9ICgobHopIC0gKGh6KSk7CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV85ID0gbm9ybWFsaXplKGx4diwgbHl2LCBsenYpOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHggPSBfX3B5dHJhX3R1cGxlXzlbMF07CiAgICAgICAgICAgICAgICAgICAgbGV0IGxkeSA9IF9fcHl0cmFfdHVwbGVfOVsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgbGR6ID0gX19weXRyYV90dXBsZV85WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90bCA9IE1hdGgubWF4KGxkeSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbGRpc3QyID0gKCgoKCgobHh2KSAqIChseHYpKSkgKyAoKChseXYpICogKGx5dikpKSkpICsgKCgobHp2KSAqIChsenYpKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBnbG93ID0gKCg4LjApIC8gKCgoMS4wKSArIChsZGlzdDIpKSkpOwogICAgICAgICAgICAgICAgICAgIHIgPSAoKCgoYmFzZV9yKSArICgoKDAuOCkgKiAoZ2xvdykpKSkpICsgKCgoMC4yKSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9ICgoKChiYXNlX2cpICsgKCgoMC41KSAqIChnbG93KSkpKSkgKyAoKCgwLjE4KSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICAgICAgYiA9ICgoKChiYXNlX2IpICsgKCgoMS4wKSAqIChnbG93KSkpKSkgKyAoKCgwLjI0KSAqIChuZG90bCkpKSk7CiAgICAgICAgICAgICAgICB9IGVsc2UgewogICAgICAgICAgICAgICAgICAgIGxldCBjeCA9IDAuMDsKICAgICAgICAgICAgICAgICAgICBsZXQgY3kgPSAwLjA7CiAgICAgICAgICAgICAgICAgICAgbGV0IGN6ID0gMC4wOwogICAgICAgICAgICAgICAgICAgIGxldCByYWQgPSAxLjA7CiAgICAgICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGhpdF9raW5kKSA9PT0gKDIpKSkpIHsKICAgICAgICAgICAgICAgICAgICAgICAgY3ggPSBzMHg7CiAgICAgICAgICAgICAgICAgICAgICAgIGN5ID0gczB5OwogICAgICAgICAgICAgICAgICAgICAgICBjeiA9IHMwejsKICAgICAgICAgICAgICAgICAgICAgICAgcmFkID0gMC42NTsKICAgICAgICAgICAgICAgICAgICB9IGVsc2UgewogICAgICAgICAgICAgICAgICAgICAgICBpZiAocHlCb29sKCgoaGl0X2tpbmQpID09PSAoMykpKSkgewogICAgICAgICAgICAgICAgICAgICAgICAgICAgY3ggPSBzMXg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjeSA9IHMxeTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGN6ID0gczF6OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgcmFkID0gMC43MjsKICAgICAgICAgICAgICAgICAgICAgICAgfSBlbHNlIHsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGN4ID0gczJ4OwogICAgICAgICAgICAgICAgICAgICAgICAgICAgY3kgPSBzMnk7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBjeiA9IHMyejsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHJhZCA9IDAuNTg7CiAgICAgICAgICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgICAgICB9CiAgICAgICAgICAgICAgICAgICAgbGV0IGh4ID0gKChjYW1feCkgKyAoKChiZXN0X3QpICogKGR4KSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgaHkgPSAoKGNhbV95KSArICgoKGJlc3RfdCkgKiAoZHkpKSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBoeiA9ICgoY2FtX3opICsgKCgoYmVzdF90KSAqIChkeikpKSk7CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV8xMCA9IG5vcm1hbGl6ZSgoKCgoaHgpIC0gKGN4KSkpIC8gKHJhZCkpLCAoKCgoaHkpIC0gKGN5KSkpIC8gKHJhZCkpLCAoKCgoaHopIC0gKGN6KSkpIC8gKHJhZCkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbnggPSBfX3B5dHJhX3R1cGxlXzEwWzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBueSA9IF9fcHl0cmFfdHVwbGVfMTBbMV07CiAgICAgICAgICAgICAgICAgICAgbGV0IG56ID0gX19weXRyYV90dXBsZV8xMFsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzExID0gcmVmbGVjdChkeCwgZHksIGR6LCBueCwgbnksIG56KTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR4ID0gX19weXRyYV90dXBsZV8xMVswXTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR5ID0gX19weXRyYV90dXBsZV8xMVsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgcmR6ID0gX19weXRyYV90dXBsZV8xMVsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzEyID0gcmVmcmFjdChkeCwgZHksIGR6LCBueCwgbnksIG56LCAoKDEuMCkgLyAoMS40NSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR4ID0gX19weXRyYV90dXBsZV8xMlswXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR5ID0gX19weXRyYV90dXBsZV8xMlsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGR6ID0gX19weXRyYV90dXBsZV8xMlsyXTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzEzID0gc2t5X2NvbG9yKHJkeCwgcmR5LCByZHosIHRwaGFzZSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IHNyID0gX19weXRyYV90dXBsZV8xM1swXTsKICAgICAgICAgICAgICAgICAgICBsZXQgc2cgPSBfX3B5dHJhX3R1cGxlXzEzWzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBzYiA9IF9fcHl0cmFfdHVwbGVfMTNbMl07CiAgICAgICAgICAgICAgICAgICAgY29uc3QgX19weXRyYV90dXBsZV8xNCA9IHNreV9jb2xvcih0ZHgsIHRkeSwgdGR6LCAoKHRwaGFzZSkgKyAoMC44KSkpOwogICAgICAgICAgICAgICAgICAgIGxldCB0ciA9IF9fcHl0cmFfdHVwbGVfMTRbMF07CiAgICAgICAgICAgICAgICAgICAgbGV0IHRnID0gX19weXRyYV90dXBsZV8xNFsxXTsKICAgICAgICAgICAgICAgICAgICBsZXQgdGIgPSBfX3B5dHJhX3R1cGxlXzE0WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBjb3NpID0gTWF0aC5tYXgoKC0oKCgoKCgoZHgpICogKG54KSkpICsgKCgoZHkpICogKG55KSkpKSkgKyAoKChkeikgKiAobnopKSkpKSksIDAuMCk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGZyID0gc2NobGljayhjb3NpLCAwLjA0KTsKICAgICAgICAgICAgICAgICAgICByID0gKCgoKHRyKSAqICgoKDEuMCkgLSAoZnIpKSkpKSArICgoKHNyKSAqIChmcikpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9ICgoKCh0ZykgKiAoKCgxLjApIC0gKGZyKSkpKSkgKyAoKChzZykgKiAoZnIpKSkpOwogICAgICAgICAgICAgICAgICAgIGIgPSAoKCgodGIpICogKCgoMS4wKSAtIChmcikpKSkpICsgKCgoc2IpICogKGZyKSkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHh2ID0gKChseCkgLSAoaHgpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHl2ID0gKChseSkgLSAoaHkpKTsKICAgICAgICAgICAgICAgICAgICBsZXQgbHp2ID0gKChseikgLSAoaHopKTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzE1ID0gbm9ybWFsaXplKGx4diwgbHl2LCBsenYpOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHggPSBfX3B5dHJhX3R1cGxlXzE1WzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHkgPSBfX3B5dHJhX3R1cGxlXzE1WzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBsZHogPSBfX3B5dHJhX3R1cGxlXzE1WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90bCA9IE1hdGgubWF4KCgoKCgoKG54KSAqIChsZHgpKSkgKyAoKChueSkgKiAobGR5KSkpKSkgKyAoKChueikgKiAobGR6KSkpKSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBjb25zdCBfX3B5dHJhX3R1cGxlXzE2ID0gbm9ybWFsaXplKCgobGR4KSAtIChkeCkpLCAoKGxkeSkgLSAoZHkpKSwgKChsZHopIC0gKGR6KSkpOwogICAgICAgICAgICAgICAgICAgIGxldCBodnggPSBfX3B5dHJhX3R1cGxlXzE2WzBdOwogICAgICAgICAgICAgICAgICAgIGxldCBodnkgPSBfX3B5dHJhX3R1cGxlXzE2WzFdOwogICAgICAgICAgICAgICAgICAgIGxldCBodnogPSBfX3B5dHJhX3R1cGxlXzE2WzJdOwogICAgICAgICAgICAgICAgICAgIGxldCBuZG90aCA9IE1hdGgubWF4KCgoKCgoKG54KSAqIChodngpKSkgKyAoKChueSkgKiAoaHZ5KSkpKSkgKyAoKChueikgKiAoaHZ6KSkpKSwgMC4wKTsKICAgICAgICAgICAgICAgICAgICBsZXQgc3BlYyA9ICgobmRvdGgpICogKG5kb3RoKSk7CiAgICAgICAgICAgICAgICAgICAgc3BlYyA9ICgoc3BlYykgKiAoc3BlYykpOwogICAgICAgICAgICAgICAgICAgIHNwZWMgPSAoKHNwZWMpICogKHNwZWMpKTsKICAgICAgICAgICAgICAgICAgICBzcGVjID0gKChzcGVjKSAqIChzcGVjKSk7CiAgICAgICAgICAgICAgICAgICAgbGV0IGdsb3cgPSAoKDEwLjApIC8gKCgoKCgoKDEuMCkgKyAoKChseHYpICogKGx4dikpKSkpICsgKCgobHl2KSAqIChseXYpKSkpKSArICgoKGx6dikgKiAobHp2KSkpKSkpOwogICAgICAgICAgICAgICAgICAgIHIgPSByICsgKCgoKCgoMC4yKSAqIChuZG90bCkpKSArICgoKDAuOCkgKiAoc3BlYykpKSkpICsgKCgoMC40NSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgZyA9IGcgKyAoKCgoKCgwLjE4KSAqIChuZG90bCkpKSArICgoKDAuNikgKiAoc3BlYykpKSkpICsgKCgoMC4zNSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgYiA9IGIgKyAoKCgoKCgwLjI2KSAqIChuZG90bCkpKSArICgoKDEuMCkgKiAoc3BlYykpKSkpICsgKCgoMC42NSkgKiAoZ2xvdykpKSk7CiAgICAgICAgICAgICAgICAgICAgaWYgKHB5Qm9vbCgoKGhpdF9raW5kKSA9PT0gKDIpKSkpIHsKICAgICAgICAgICAgICAgICAgICAgICAgciA9IHIgKiAwLjk1OwogICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDEuMDU7CiAgICAgICAgICAgICAgICAgICAgICAgIGIgPSBiICogMS4xOwogICAgICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIChweUJvb2woKChoaXRfa2luZCkgPT09ICgzKSkpKSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICByID0gciAqIDEuMDg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDAuOTg7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBiID0gYiAqIDEuMDQ7CiAgICAgICAgICAgICAgICAgICAgICAgIH0gZWxzZSB7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICByID0gciAqIDEuMDI7CiAgICAgICAgICAgICAgICAgICAgICAgICAgICBnID0gZyAqIDEuMTsKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGIgPSBiICogMC45NTsKICAgICAgICAgICAgICAgICAgICAgICAgfQogICAgICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgICAgIH0KICAgICAgICAgICAgfQogICAgICAgICAgICByID0gbWF0aC5zcXJ0KGNsYW1wMDEocikpOwogICAgICAgICAgICBnID0gbWF0aC5zcXJ0KGNsYW1wMDEoZykpOwogICAgICAgICAgICBiID0gbWF0aC5zcXJ0KGNsYW1wMDEoYikpOwogICAgICAgICAgICBmcmFtZVtpXSA9IHF1YW50aXplXzMzMihyLCBnLCBiKTsKICAgICAgICAgICAgaSA9IGkgKyAxOwogICAgICAgIH0KICAgIH0KICAgIHJldHVybiBweUJ5dGVzKGZyYW1lKTsKfQpmdW5jdGlvbiBydW5fMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zKCkgewogICAgbGV0IHdpZHRoID0gMzIwOwogICAgbGV0IGhlaWdodCA9IDI0MDsKICAgIGxldCBmcmFtZXNfbiA9IDcyOwogICAgbGV0IG91dF9wYXRoID0gJ3NhbXBsZS9vdXQvMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zLmdpZic7CiAgICBsZXQgc3RhcnQgPSBwZXJmX2NvdW50ZXIoKTsKICAgIGxldCBmcmFtZXMgPSBbXTsKICAgIGxldCBpOwogICAgZm9yIChsZXQgX19weXRyYV9pXzE3ID0gMDsgX19weXRyYV9pXzE3IDwgZnJhbWVzX247IF9fcHl0cmFfaV8xNyArPSAxKSB7CiAgICAgICAgaSA9IF9fcHl0cmFfaV8xNzsKICAgICAgICBmcmFtZXMucHVzaChyZW5kZXJfZnJhbWUod2lkdGgsIGhlaWdodCwgaSwgZnJhbWVzX24pKTsKICAgIH0KICAgIHNhdmVfZ2lmKG91dF9wYXRoLCB3aWR0aCwgaGVpZ2h0LCBmcmFtZXMsIHBhbGV0dGVfMzMyKCksIDYsIDApOwogICAgbGV0IGVsYXBzZWQgPSAoKHBlcmZfY291bnRlcigpKSAtIChzdGFydCkpOwogICAgcHlQcmludCgnb3V0cHV0OicsIG91dF9wYXRoKTsKICAgIHB5UHJpbnQoJ2ZyYW1lczonLCBmcmFtZXNfbik7CiAgICBweVByaW50KCdlbGFwc2VkX3NlYzonLCBlbGFwc2VkKTsKfQpydW5fMTZfZ2xhc3Nfc2N1bHB0dXJlX2NoYW9zKCk7Cg=="

        // エントリポイント。
        @JvmStatic
        fun main(args: Array<String>) {
            val code = PyRuntime.runEmbeddedNode(PYTRA_EMBEDDED_JS_BASE64, args)
            kotlin.system.exitProcess(code)
        }
    }
}
```
</details>

</details>

## ドキュメント

利用時によく参照する順で、関連ドキュメントをまとめています。

- まず使い方を確認する: [docs/how-to-use.md](docs/how-to-use.md)
- 実装済み項目・未実装項目・対応予定なしを確認する: [docs/pytra-readme.md](docs/pytra-readme.md)
- サンプル一覧と概要を確認する: [docs/sample-code.md](docs/sample-code.md)
- 仕様・制約・構成・運用ルールを確認する: [docs/spec.md](docs/spec.md)

## ライセンス

MIT License
