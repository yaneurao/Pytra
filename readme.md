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

|ファイル名|内容|Python| C++ | Rust | C# | JS | TypeScript |
|-|-|-:|-:|-:|-|-|-|
|01_mandelbrot|マンデルブロ集合（PNG）|16.175|0.726|0.733|2.549|🚧|🚧|
|02_raytrace_spheres|球の簡易レイトレーサ（PNG）|5.132|0.142|0.147|0.865|🚧|🚧|
|03_julia_set|ジュリア集合（PNG）|13.578|0.794|0.673|3.395|🚧|🚧|
|04_monte_carlo_pi|モンテカルロ法で円周率近似|10.921|0.155|0.193|0.601|🚧|🚧|
|05_mandelbrot_zoom|マンデルブロズーム（GIF）|13.802|0.525|0.532|2.694|🚧|🚧|
|06_julia_parameter_sweep|ジュリア集合パラメータ掃引（GIF）|9.825|0.383|0.375|1.929|🚧|🚧|
|07_game_of_life_loop|ライフゲーム（GIF）|13.410|0.717|1.421|3.167|🚧|🚧|
|08_langtons_ant|ラングトンのアリ（GIF）|7.431|0.483|1.766|2.233|🚧|🚧|
|09_fire_simulation|炎シミュレーション（GIF）|13.649|0.638|7.756|6.488|🚧|🚧|
|10_plasma_effect|プラズマエフェクト（GIF）|7.640|0.673|0.539|2.356|🚧|🚧|
|11_lissajous_particles|リサージュ粒子（GIF）|5.250|0.382|0.347|0.754|🚧|🚧|
|12_sort_visualizer|ソート可視化（GIF）|11.451|0.723|0.696|1.852|🚧|🚧|
|13_maze_generation_steps|迷路生成ステップ（GIF）|4.716|0.302|0.279|0.946|🚧|🚧|
|14_raymarching_light_cycle|簡易レイマーチング（GIF）|2.666|0.152|0.150|0.467|🚧|🚧|
|15_mini_language_interpreter|ミニ言語インタプリタ |2.207|0.577|1.378|1.035|🚧|🚧|
|16_glass_sculpture_chaos|ガラス彫刻のカオス回転（GIF）|7.114|0.250|0.233|1.289|🚧|🚧|

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

string palette_332()
{
    string p = py_bytearray((256 * 3));
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

string render_frame(long long width, long long height, long long frame_id, long long frames_n)
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
    string frame = py_bytearray((width * height));
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
    vector<string> frames = {};
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

## 使い方について

実際の使い方については [docs/how-to-use.md](docs/how-to-use.md) をご覧ください。


## 実装済みの言語機能

- 変数代入（通常代入、型注釈付き代入、拡張代入の主要ケース）
- 算術・ビット演算（`+ - * / // % ** & | ^ << >>` の主要ケース）
- 比較演算（`== != < <= > >= in not in is is not` の主要ケース）
- 論理演算（`and or not`）
- 単項演算（`+x -x ~x`）
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

## 実装済みの組み込み関数

- `print`
- `len`
- `range`（主に `for ... in range(...)`）
- `int`
- `float`
- `str`
- `ord`
- `bytes`
- `bytearray`
- `min`
- `max`

## 対応module

Python標準ライブラリ

- `math`（主要関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `floor`, `ceil`, `pow` など）
- `time`（`perf_counter`）
- `pathlib`（利用中機能の範囲）
- `dataclasses`（`@dataclass`）
- `ast`（セルフホスティングのためのランタイム実装）

独自追加ライブラリ

- `py_module.png_helper` : PNG画像出力ヘルパ
- `py_module.gif_helper` : GIF画像出力ヘルパ

## 作業中

- C++, C#, Rust以外の言語へのトランスパイラ本体
- a[b:c] 以外のスライス構文
- その他、詳しくは、[docs/todo.md](docs/todo.md) に書いています。

## 未実装項目

- 標準ライブラリ網羅対応（`import` 可能モジュールの拡充）
- 例外処理・型推論の高度化

## 対応予定なし

- Python 構文の完全互換（現状はサブセット）
- 動的なimport
- 動的な型付け
- 弱参照, 循環参照
- スライスオブジェクト(コピーされる実装)


## 開発について

本トランスパイラは、主にGPT-5.3-Codexで開発しています。


## ライセンス

MIT License
