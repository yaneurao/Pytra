#include "cpp_module/py_runtime.h"

// 11: リサージュ運動する粒子をGIF出力するサンプル。

bytes color_palette() {
    bytearray p = bytearray{};
    for (int64 i = 0; i < 256; ++i) {
        int64 r = i;
        int64 g = i * 3 % 256;
        int64 b = 255 - i;
        p.append(r);
        p.append(g);
        p.append(b);
    }
    return bytes(p);
}

void run_11_lissajous_particles() {
    int64 w = 320;
    int64 h = 240;
    int64 frames_n = 360;
    int64 particles = 48;
    str out_path = "sample/out/11_lissajous_particles.gif";
    
    auto start = perf_counter();
    list<bytes> frames = list<bytes>{};
    
    for (int64 t = 0; t < frames_n; ++t) {
        bytearray frame = bytearray(w * h);
        
        for (int64 p = 0; p < particles; ++p) {
            float64 phase = static_cast<float64>(p) * 0.261799;
            int64 x = py_to_int64(static_cast<float64>(w) * 0.5 + static_cast<float64>(w) * 0.38 * py_math::sin(0.11 * static_cast<float64>(t) + phase * 2.0));
            int64 y = py_to_int64(static_cast<float64>(h) * 0.5 + static_cast<float64>(h) * 0.38 * py_math::sin(0.17 * static_cast<float64>(t) + phase * 3.0));
            int64 color = 30 + p * 9 % 220;
            
            for (int64 dy = -2; dy < 3; ++dy) {
                for (int64 dx = -2; dx < 3; ++dx) {
                    int64 xx = x + dx;
                    int64 yy = y + dy;
                    if ((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)) {
                        int64 d2 = dx * dx + dy * dy;
                        if (d2 <= 4) {
                            int64 idx = yy * w + xx;
                            int64 v = color - d2 * 20;
                            v = py_max(0, v);
                            if (v > frame[idx])
                                frame[idx] = v;
                        }
                    }
                }
            }
        }
        
        frames.append(bytes(frame));
    }
    
    // bridge: Python gif_helper.save_gif -> C++ runtime save_gif
    save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    auto elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_11_lissajous_particles();
    return 0;
}
