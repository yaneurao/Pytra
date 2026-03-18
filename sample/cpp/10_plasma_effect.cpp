#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "generated/built_in/io_ops.h"
#include "generated/std/math.h"
#include "generated/std/time.h"
#include "generated/utils/gif.h"

// 10: Sample that outputs a plasma effect as a GIF.

void run_10_plasma_effect() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 216;
    str out_path = "sample/out/10_plasma_effect.gif";
    
    float64 start = pytra::std::time::perf_counter();
    rc<list<bytes>> frames = rc_list_from_value(list<bytes>{});
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        for (int64 y = 0; y < h; ++y) {
            int64 row_base = y * w;
            for (int64 x = 0; x < w; ++x) {
                int64 dx = x - 160;
                int64 dy = y - 120;
                float64 v = pytra::std::math::sin((float64(x) + float64(t) * 2.0) * 0.045) + pytra::std::math::sin((float64(y) - float64(t) * 1.2) * 0.05) + pytra::std::math::sin((float64(x + y) + float64(t) * 1.7) * 0.03) + pytra::std::math::sin(pytra::std::math::sqrt(dx * dx + dy * dy) * 0.07 - float64(t) * 0.18);
                int64 c = int64((v + 4.0) * (255.0 / 8.0));
                if (c < 0)
                    c = 0;
                if (c > 255)
                    c = 255;
                frame[row_base + x] = c;
            }
        }
        rc_list_ref(frames).append(frame);
    }
    pytra::utils::gif::save_gif(out_path, w, h, rc_list_ref(frames), pytra::utils::gif::grayscale_palette(), 3, 0);
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
