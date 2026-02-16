# Pytraとは何？

Pytraは、Pythonのサブセットで書かれたプログラムを様々な言語に変換するためのトランスパイラ群です。

現在は Python から C++/C#/Rust への変換に対応しており、JavaScript/TypeScript/Go/Java/Swift/Kotlin は対応予定です。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

⚠ Pythonで書いたプログラム丸ごとを移植できることは期待しないでください。「Pythonで書いたコアコードが上手く変換されたらラッキーだな」ぐらいの温度感でお使いください。

## 開発動機

マルチプラットフォーム対応のゲームを作ろうと思うと、現在は、Unityが現実解です。UnityではC#で書く必要があります。私はサーバーサイドは、Pythonで書きたかったのですが、ブラウザ側もあるなら、そこはJavaScriptで書く必要があります。

こうなると3つの言語を行き来して、同じロジックを3回実装しなければなりません。「これはさすがにおかしいのでは？」と思ったのが本トランスパイラの開発のきっかけです。

また、素のPythonだと遅すぎてサーバーサイドで大量のリクエストを捌くのには向かないです。ここが少しでも速くなればと思い、開発しました。

JavaScriptのコードにも変換できるので、Pythonでブラウザゲームの開発もできます。


## 実行速度の比較

サンプルコード(Pythonで書かれている)の実行時間と、そのトランスパイルしたソースコードでの実行時間。（単位: 秒）

💡 元のソースコード、変換されたソースコード、計測条件等については、[docs/time-comparison.md](docs/time-comparison.md) をご覧ください。

|ファイル名|内容|Python| C++ | C# | Rust | JS | TypeScript |
|-|-|-:|-:|-:|-|-|-|
|01_mandelbrot|マンデルブロ集合（PNG）|1.689|0.089|0.078|0.124|🚧|🚧|
|02_raytrace_spheres|球の簡易レイトレーサ（PNG）|0.414|0.030|0.121|0.054|🚧|🚧|
|03_julia_set|ジュリア集合（PNG）|1.380|0.087|0.141|0.110|🚧|🚧|
|04_monte_carlo_pi|モンテカルロ法で円周率近似|3.657|0.052|0.200|0.066|🚧|🚧|
|05_mandelbrot_zoom|マンデルブロズーム（GIF）|13.802|0.525|2.694|0.529|🚧|🚧|
|06_julia_parameter_sweep|ジュリア集合パラメータ掃引（GIF）|9.825|0.383|1.929|0.385|🚧|🚧|
|07_game_of_life_loop|ライフゲーム（GIF）|1.290|0.067|0.314|0.109|🚧|🚧|
|08_langtons_ant|ラングトンのアリ（GIF）|0.744|0.050|0.234|0.145|🚧|🚧|
|09_fire_simulation|炎シミュレーション（GIF）|1.088|0.054|0.522|0.435|🚧|🚧|
|10_plasma_effect|プラズマエフェクト（GIF）|2.419|0.221|0.769|0.184|🚧|🚧|
|11_lissajous_particles|リサージュ粒子（GIF）|1.118|0.081|0.163|0.076|🚧|🚧|
|12_sort_visualizer|ソート可視化（GIF）|3.471|0.233|0.465|0.220|🚧|🚧|
|13_maze_generation_steps|迷路生成ステップ（GIF）|0.521|0.033|0.113|0.037|🚧|🚧|
|14_raymarching_light_cycle|簡易レイマーチング（GIF）|2.666|0.152|0.467|0.152|🚧|🚧|
|15_mini_language_interpreter|ミニ言語インタプリタ |2.207|0.577|1.035|🚧|🚧|🚧|

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
    for i in range(frames_n):
        t = i / frames_n
        angle = 2.0 * math.pi * t
        cr = center_cr + radius_cr * math.cos(angle)
        ci = center_ci + radius_ci * math.sin(angle)
        phase = (i * 5) % 255
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

string julia_palette()
{
    string palette = py_bytearray((256 * 3));
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

string render_frame(long long width, long long height, double cr, double ci, long long max_iter, long long phase)
{
    string frame = py_bytearray((width * height));
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
    vector<string> frames = {};
    double center_cr = (-0.745);
    double center_ci = 0.186;
    double radius_cr = 0.12;
    double radius_ci = 0.1;
    auto __pytra_range_start_10 = 0;
    auto __pytra_range_stop_11 = frames_n;
    auto __pytra_range_step_12 = 1;
    if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
    {
        double t = py_div(i, frames_n);
        double angle = ((2.0 * pycs::cpp_module::math::pi) * t);
        auto cr = (center_cr + (radius_cr * pycs::cpp_module::math::cos(angle)));
        auto ci = (center_ci + (radius_ci * pycs::cpp_module::math::sin(angle)));
        long long phase = ((i * 5) % 255);
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
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = frames_n;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
        {
            var t = ((double)(i) / (double)(frames_n));
            var angle = ((2.0 * Math.PI) * t);
            var cr = (center_cr + (radius_cr * Math.Cos(angle)));
            var ci = (center_ci + (radius_ci * Math.Sin(angle)));
            var phase = ((i * 5L) % 255L);
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
<summary>Rustへの変換例 : 06_julia_parameter_sweep.rs</summary>

```rust
#[path = "../../src/rs_module/py_runtime.rs"]
mod py_runtime;
use py_runtime::{math_cos, math_exp, math_sin, math_sqrt, perf_counter, py_bool, py_grayscale_palette, py_in, py_isalpha, py_isdigit, py_len, py_print, py_save_gif, py_slice, py_write_rgb_png};

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
    for i in (0)..(frames_n) {
        let mut t = ((( i ) as f64) / (( frames_n ) as f64));
        let mut angle = ((((2.0) * (std::f64::consts::PI))) * (t));
        let mut cr = ((center_cr) + (((radius_cr) * (math_cos(((angle) as f64))))));
        let mut ci = ((center_ci) + (((radius_ci) * (math_sin(((angle) as f64))))));
        let mut phase = ((((i) * (5))) % (255));
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


## 使い方について

実際の使い方については [docs/how-to-use.md](docs/how-to-use.md) をご覧ください。


## 実装済みの言語機能

- 変数代入（通常代入、型注釈付き代入、拡張代入の主要ケース）
- 算術演算（`+ - * / // % **` の主要ケース）
- 比較演算（`== != < <= > >= in not in is is not` の主要ケース）
- 条件分岐（`if / elif / else`）
- ループ（`while`、`for in <iterable>`、`for in range(...)`）
- 例外（`try/except/finally`、`raise` の主要ケース）
- 関数定義・関数呼び出し・戻り値
- クラス定義（単一継承、`__init__`、static member、instance member）
- `@dataclass` の基本変換
- 文字列（f-string の主要ケース、`replace` などの主要メソッド）
- コンテナ（`list`, `dict`, `set`, `tuple` の主要ケース）
- list/set comprehension の主要ケース
- `if __name__ == "__main__":` ガードの認識
- 型マッピング（`int`, `int8..uint64`, `float`, `float32`, `str`, `bool`, `None`）
- for ～ in , for ～ in range()構文
- a[b:c] 形式のスライス構文

## 組み込み関数

かきかけ

### module

- `math`（主要関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `floor`, `ceil`, `pow` など）
- `time`（`perf_counter`）
- `pathlib`（利用中機能の範囲）
- `dataclasses`（`@dataclass`）
- `ast`（セルフホスティングのためのランタイム実装）

独自追加。
- `py_module.png_helper` : PNG画像出力ヘルパ
- `py_module.gif_helper` : GIF画像出力ヘルパ

## 作業中

- C++, C#, Rust以外の言語へのトランスパイラ本体
- a[b:c] 以外のスライス構文
- その他、詳しくは、[docs/todo.md](docs/todo.md) に書いてます。

## 未実装項目

- 標準ライブラリ網羅対応（`import` 可能モジュールの拡充）
- 例外処理・型推論の高度化

## 対応予定なし

- Python 構文の完全互換（現状はサブセット）
- 動的なimport
- 動的な型付け
- 弱参照, 循環参照 非対応
- スライスオブジェクト


## 開発について

本トランスパイラは、主にGPT-5.3-Codexで開発しています。

## ライセンス

MIT License
