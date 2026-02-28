#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 08: Sample that outputs Langton's Ant trajectories as a GIF.

bytes capture(const object& grid, int64 w, int64 h) {
    bytearray frame = bytearray(w * h);
    for (int64 y = 0; y < h; ++y) {
        int64 row_base = y * w;
        for (int64 x = 0; x < w; ++x) {
            frame[row_base + x] = (int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(y))), py_to<int64>(x)))) ? 255 : 0);
        }
    }
    return bytes(frame);
}

void run_08_langtons_ant() {
    int64 w = 420;
    int64 h = 420;
    str out_path = "sample/out/08_langtons_ant.gif";
    
    float64 start = pytra::std::time::perf_counter();
    
    object grid = [&]() -> object {     list<object> __out;     for (int64 _ = 0; (_ < h); _ += (1)) {         __out.append(make_object(py_repeat(list<int64>(make_object(list<int64>{0})), w)));     }     return make_object(__out); }();
    int64 x = w / 2;
    int64 y = h / 2;
    int64 d = 0;
    
    int64 steps_total = 600000;
    int64 capture_every = 3000;
    object frames = make_object(list<object>{});
    
    for (int64 i = 0; i < steps_total; ++i) {
        if (int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(y))), py_to<int64>(x)))) == 0) {
            d = (d + 1) % 4;
            py_set_at(object(py_at(grid, py_to<int64>(y))), x, make_object(1));
        } else {
            d = (d + 3) % 4;
            py_set_at(object(py_at(grid, py_to<int64>(y))), x, make_object(0));
        }
        if (d == 0) {
            y = (y - 1 + h) % h;
        } else {
            if (d == 1) {
                x = (x + 1) % w;
            } else {
                if (d == 2)
                    y = (y + 1) % h;
                else
                    x = (x - 1 + w) % w;
            }
        }
        if (i % capture_every == 0)
            py_append(frames, make_object(capture(grid, w, h)));
    }
    pytra::utils::gif::save_gif(out_path, w, h, frames, pytra::utils::gif::grayscale_palette(), 5, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_08_langtons_ant();
    return 0;
}
