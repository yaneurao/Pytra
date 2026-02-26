#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 09: Sample that outputs a simple fire effect as a GIF.

bytes fire_palette() {
    bytearray p = bytearray{};
    for (int64 i = 0; i < 256; ++i) {
        int64 r = 0;
        int64 g = 0;
        int64 b = 0;
        if (i < 85) {
            r = i * 3;
            g = 0;
            b = 0;
        } else {
            if (i < 170) {
                r = 255;
                g = (i - 85) * 3;
                b = 0;
            } else {
                r = 255;
                g = 255;
                b = (i - 170) * 3;
            }
        }
        p.append(r);
        p.append(g);
        p.append(b);
    }
    return bytes(p);
}

void run_09_fire_simulation() {
    int64 w = 380;
    int64 h = 260;
    int64 steps = 420;
    str out_path = "sample/out/09_fire_simulation.gif";
    
    auto start = pytra::std::time::perf_counter();
    list<list<int64>> heat = [&]() -> list<list<int64>> {     list<list<int64>> __out;     for (int64 _ = 0; (_ < h); _ += (1)) {         __out.append(make_object(py_repeat(list<int64>{0}, w)));     }     return __out; }();
    list<bytes> frames = list<bytes>{};
    
    for (int64 t = 0; t < steps; ++t) {
        for (int64 x = 0; x < w; ++x) {
            int64 val = 170 + (x * 13 + t * 17) % 86;
            heat[h - 1][x] = val;
        }
        for (int64 y = 1; y < h; ++y) {
            for (int64 x = 0; x < w; ++x) {
                int64 a = heat[y][x];
                int64 b = heat[y][(x - 1 + w) % w];
                int64 c = heat[y][(x + 1) % w];
                int64 d = heat[(y + 1) % h][x];
                int64 v = (a + b + c + d) / 4;
                int64 cool = 1 + (x + y + t) % 3;
                int64 nv = v - cool;
                heat[y - 1][x] = (nv > 0 ? nv : 0);
            }
        }
        bytearray frame = bytearray(w * h);
        for (int64 yy = 0; yy < h; ++yy) {
            int64 row_base = yy * w;
            for (int64 xx = 0; xx < w; ++xx) {
                frame[row_base + xx] = heat[yy][xx];
            }
        }
        frames.append(bytes(frame));
    }
    pytra::utils::gif::save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    auto elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_09_fire_simulation();
    return 0;
}
