#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/math.h"
#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 10: Sample that outputs a plasma effect as a GIF.

void run_10_plasma_effect() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 216;
    str out_path = "sample/out/10_plasma_effect.gif";
    
    float64 start = pytra::std::time::perf_counter();
    object frames = make_object(list<object>{});
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        for (int64 y = 0; y < h; ++y) {
            int64 row_base = y * w;
            for (int64 x = 0; x < w; ++x) {
                int64 dx = x - 160;
                int64 dy = y - 120;
                float64 v = pytra::std::math::sin((py_to<float64>(x) + py_to<float64>(t) * 2.0) * 0.045) + pytra::std::math::sin((py_to<float64>(y) - py_to<float64>(t) * 1.2) * 0.05) + pytra::std::math::sin((py_to<float64>(x + y) + py_to<float64>(t) * 1.7) * 0.03) + pytra::std::math::sin(pytra::std::math::sqrt(dx * dx + dy * dy) * 0.07 - py_to<float64>(t) * 0.18);
                int64 c = int64((v + 4.0) * (py_div(255.0, 8.0)));
                if (c < 0)
                    c = 0;
                if (c > 255)
                    c = 255;
                frame[row_base + x] = c;
            }
        }
        py_append(frames, make_object(bytes(frame)));
    }
    pytra::utils::gif::save_gif(out_path, w, h, frames, pytra::utils::gif::grayscale_palette(), 3, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_10_plasma_effect();
    return 0;
}
