#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"
#include "generated/built_in/io_ops.h"
#include "generated/built_in/numeric_ops.h"
#include "generated/std/math.h"
#include "generated/std/time.h"
#include "generated/utils/gif.h"

// 11: Sample that outputs Lissajous-motion particles as a GIF.

bytes color_palette() {
    bytearray p = bytearray{};
    for (int64 i = 0; i < 256; ++i) {
        int64 r = i;
        int64 g = i * 3 % 256;
        int64 b = 255 - i;
        p.append(uint8(r));
        p.append(uint8(g));
        p.append(uint8(b));
    }
    return p;
}

void run_11_lissajous_particles() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 360;
    int64 particles = 48;
    str out_path = "sample/out/11_lissajous_particles.gif";
    
    float64 start = pytra::std::time::perf_counter();
    rc<list<bytes>> frames = rc_list_from_value(list<bytes>{});
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        float64 __hoisted_cast_1 = float64(t);
        
        for (int64 p = 0; p < particles; ++p) {
            float64 phase = float64(p) * 0.261799;
            int64 x = int64(float64(w) * 0.5 + float64(w) * 0.38 * pytra::std::math::sin(0.11 * __hoisted_cast_1 + phase * 2.0));
            int64 y = int64(float64(h) * 0.5 + float64(h) * 0.38 * pytra::std::math::sin(0.17 * __hoisted_cast_1 + phase * 3.0));
            int64 color = 30 + p * 9 % 220;
            
            for (int64 dy = -(2); dy < 3; ++dy) {
                for (int64 dx = -(2); dx < 3; ++dx) {
                    int64 xx = x + dx;
                    int64 yy = y + dy;
                    if ((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)) {
                        int64 d2 = dx * dx + dy * dy;
                        if (d2 <= 4) {
                            int64 idx = yy * w + xx;
                            int64 v = color - d2 * 20;
                            v = ::std::max<int64>(0, v);
                            if (v > frame[idx])
                                frame[idx] = uint8(v);
                        }
                    }
                }
            }
        }
        rc_list_ref(frames).append(frame);
    }
    pytra::utils::gif::save_gif(out_path, w, h, rc_list_ref(frames), color_palette(), 3, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_11_lissajous_particles();
    return 0;
}
