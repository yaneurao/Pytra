#include "cpp_module/py_runtime.h"

// 10: プラズマエフェクトをGIF出力するサンプル。

void run_10_plasma_effect() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 216;
    str out_path = "sample/out/10_plasma_effect.gif";
    
    auto start = perf_counter();
    list<bytes> frames = list<bytes>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        int64 i = 0;
        for (int64 y = 0; y < h; ++y) {
            for (int64 x = 0; x < w; ++x) {
                int64 dx = x - 160;
                int64 dy = y - 120;
                auto v = py_math::sin((static_cast<float64>(x) + static_cast<float64>(t) * 2.0) * 0.045) + py_math::sin((static_cast<float64>(y) - static_cast<float64>(t) * 1.2) * 0.05) + py_math::sin((static_cast<float64>(x + y) + static_cast<float64>(t) * 1.7) * 0.03) + py_math::sin(py_math::sqrt(dx * dx + dy * dy) * 0.07 - static_cast<float64>(t) * 0.18);
                
                
                
                
                
                int64 c = py_to_int64((v + 4.0) * (255.0 / 8.0));
                if (c < 0)
                    c = 0;
                if (c > 255)
                    c = 255;
                frame[i] = c;
                i++;
            }
        }
        frames.append(bytes(frame));
    }
    
    // bridge: Python gif_helper.save_gif -> C++ runtime save_gif
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    auto elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_10_plasma_effect();
    return 0;
}
