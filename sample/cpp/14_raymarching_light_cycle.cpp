#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/math.h"
#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

bytes palette() {
    bytearray p = bytearray{};
    for (int64 i = 0; i < 256; ++i) {
        int64 r = ::std::min<int64>(static_cast<int64>(255), static_cast<int64>(int64(py_to<float64>(20) + py_to<float64>(i) * 0.9)));
        int64 g = ::std::min<int64>(static_cast<int64>(255), static_cast<int64>(int64(py_to<float64>(10) + py_to<float64>(i) * 0.7)));
        int64 b = ::std::min<int64>(static_cast<int64>(255), static_cast<int64>(30 + i));
        p.append(r);
        p.append(g);
        p.append(b);
    }
    return bytes(p);
}

int64 scene(float64 x, float64 y, float64 light_x, float64 light_y) {
    float64 x1 = x + 0.45;
    float64 y1 = y + 0.2;
    float64 x2 = x - 0.35;
    float64 y2 = y - 0.15;
    float64 r1 = pytra::std::math::sqrt(x1 * x1 + y1 * y1);
    float64 r2 = pytra::std::math::sqrt(x2 * x2 + y2 * y2);
    float64 blob = pytra::std::math::exp(-7.0 * r1 * r1) + pytra::std::math::exp(-8.0 * r2 * r2);
    
    float64 lx = x - light_x;
    float64 ly = y - light_y;
    float64 l = pytra::std::math::sqrt(lx * lx + ly * ly);
    float64 lit = 1.0 / (1.0 + 3.5 * l * l);
    
    int64 v = int64(255.0 * blob * lit * 5.0);
    return ::std::min<int64>(static_cast<int64>(255), static_cast<int64>(::std::max<int64>(static_cast<int64>(0), static_cast<int64>(v))));
}

void run_14_raymarching_light_cycle() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 84;
    str out_path = "sample/out/14_raymarching_light_cycle.gif";
    
    float64 start = pytra::std::time::perf_counter();
    list<bytes> frames = list<bytes>{};
    float64 __hoisted_cast_1 = static_cast<float64>(frames_n);
    float64 __hoisted_cast_2 = static_cast<float64>(h - 1);
    float64 __hoisted_cast_3 = static_cast<float64>(w - 1);
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        auto a = (py_to<float64>(t) / __hoisted_cast_1) * pytra::std::math::pi * 2.0;
        float64 light_x = 0.75 * pytra::std::math::cos(a);
        float64 light_y = 0.55 * pytra::std::math::sin(a * 1.2);
        
        for (int64 y = 0; y < h; ++y) {
            int64 row_base = y * w;
            float64 py = (py_to<float64>(y) / __hoisted_cast_2) * 2.0 - 1.0;
            for (int64 x = 0; x < w; ++x) {
                float64 px = (py_to<float64>(x) / __hoisted_cast_3) * 2.0 - 1.0;
                frame[row_base + x] = scene(px, py, light_x, light_y);
            }
        }
        frames.append(bytes(frame));
    }
    pytra::utils::gif::save_gif(out_path, w, h, frames, palette(), 3, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_14_raymarching_light_cycle();
    return 0;
}
