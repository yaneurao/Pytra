#include "cpp_module/py_runtime.h"





void run_10_plasma_effect() {
    list<uint8> frame;
    int64 i;
    int64 dx;
    int64 dy;
    float64 v;
    int64 c;
    
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 216;
    str out_path = "sample/out/10_plasma_effect.gif";
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        frame = list<uint8>(w * h);
        i = 0;
        for (int64 y = 0; y < h; ++y) {
            for (int64 x = 0; x < w; ++x) {
                dx = x - 160;
                dy = y - 120;
                v = py_math::sin((static_cast<float64>(x) + static_cast<float64>(t) * 2.0) * 0.045) + py_math::sin((static_cast<float64>(y) - static_cast<float64>(t) * 1.2) * 0.05) + py_math::sin((static_cast<float64>(x + y) + static_cast<float64>(t) * 1.7) * 0.03) + py_math::sin(py_math::sqrt(dx * dx + dy * dy) * 0.07 - static_cast<float64>(t) * 0.18);
                c = int64((v + 4.0) * 255.0 / 8.0);
                if (c < 0)
                    c = 0;
                if (c > 255)
                    c = 255;
                frame[i] = c;
                i++;
            }
        }
        frames.push_back(list<uint8>(frame));
    }
    
    save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_10_plasma_effect();
    return 0;
}
