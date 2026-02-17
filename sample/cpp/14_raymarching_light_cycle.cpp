#include "cpp_module/py_runtime.h"

// 14: 簡易レイマーチ風の光源移動シーンをGIF出力するサンプル。

bytearray palette() {
    auto p = bytearray{};
    for (int64 i = 0; i < 256; ++i) {
        auto r = py_min(255, int64(static_cast<float64>(20) + static_cast<float64>(i) * 0.9));
        auto g = py_min(255, int64(static_cast<float64>(10) + static_cast<float64>(i) * 0.7));
        auto b = py_min(255, int64(30 + i));
        p.append(r);
        p.append(g);
        p.append(b);
    }
    return bytearray(p);
}

int64 scene(float64 x, float64 y, float64 light_x, float64 light_y) {
    float64 x1 = x + 0.45;
    float64 y1 = y + 0.2;
    float64 x2 = x - 0.35;
    float64 y2 = y - 0.15;
    auto r1 = py_math::sqrt(x1 * x1 + y1 * y1);
    auto r2 = py_math::sqrt(x2 * x2 + y2 * y2);
    auto blob = py_math::exp(-7.0 * r1 * r1) + py_math::exp(-8.0 * r2 * r2);
    
    float64 lx = x - light_x;
    float64 ly = y - light_y;
    auto l = py_math::sqrt(lx * lx + ly * ly);
    float64 lit = 1.0 / (1.0 + 3.5 * l * l);
    
    int64 v = py_to_int64(255.0 * blob * lit * 5.0);
    return py_min(255, py_max(0, v));
}

void run_14_raymarching_light_cycle() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 84;
    str out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    auto start = perf_counter();
    list<bytearray> frames = list<bytearray>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        auto frame = bytearray(w * h);
        auto a = static_cast<float64>(t) / static_cast<float64>(frames_n) * py_math::pi * 2.0;
        auto light_x = 0.75 * py_math::cos(a);
        auto light_y = 0.55 * py_math::sin(a * 1.2);
        
        int64 i = 0;
        for (int64 y = 0; y < h; ++y) {
            float64 py = static_cast<float64>(y) / (static_cast<float64>(h - 1)) * 2.0 - 1.0;
            for (int64 x = 0; x < w; ++x) {
                float64 px = static_cast<float64>(x) / (static_cast<float64>(w - 1)) * 2.0 - 1.0;
                frame[i] = scene(px, py, light_x, light_y);
                i++;
            }
        }
        
        frames.append(bytearray(frame));
    }
    
    // bridge: Python gif_helper.save_gif -> C++ runtime save_gif
    save_gif(out_path, w, h, frames, palette(), 3, 0);
    auto elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_14_raymarching_light_cycle();
    return 0;
}
