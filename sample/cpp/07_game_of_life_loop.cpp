#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 07: Sample that outputs Game of Life evolution as a GIF.

object next_state(const object& grid, int64 w, int64 h) {
    object nxt = make_object(list<object>{});
    for (int64 y = 0; y < h; ++y) {
        object row = make_object(list<object>{});
        for (int64 x = 0; x < w; ++x) {
            int64 cnt = 0;
            for (int64 dy = -1; dy < 2; ++dy) {
                for (int64 dx = -1; dx < 2; ++dx) {
                    if ((dx != 0) || (dy != 0)) {
                        int64 nx = (x + dx + w) % w;
                        int64 ny = (y + dy + h) % h;
                        cnt += int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(ny))), py_to<int64>(nx))));
                    }
                }
            }
            int64 alive = int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(y))), py_to<int64>(x))));
            if ((alive == 1) && ((cnt == 2) || (cnt == 3))) {
                py_append(row, make_object(1));
            } else {
                if ((alive == 0) && (cnt == 3))
                    py_append(row, make_object(1));
                else
                    py_append(row, make_object(0));
            }
        }
        py_append(nxt, make_object(row));
    }
    return nxt;
}

bytes render(const object& grid, int64 w, int64 h, int64 cell) {
    int64 width = w * cell;
    int64 height = h * cell;
    bytearray frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(y))), py_to<int64>(x)))) ? 255 : 0);
            for (int64 yy = 0; yy < cell; ++yy) {
                int64 base = (y * cell + yy) * width + x * cell;
                for (int64 xx = 0; xx < cell; ++xx) {
                    frame[base + xx] = v;
                }
            }
        }
    }
    return bytes(frame);
}

void run_07_game_of_life_loop() {
    int64 w = 144;
    int64 h = 108;
    int64 cell = 4;
    int64 steps = 105;
    str out_path = "sample/out/07_game_of_life_loop.gif";
    
    float64 start = pytra::std::time::perf_counter();
    object grid = [&]() -> object {     list<object> __out;     for (int64 _ = 0; (_ < h); _ += (1)) {         __out.append(make_object(py_repeat(list<int64>(make_object(list<int64>{0})), w)));     }     return make_object(__out); }();
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if (noise < 3)
                py_set_at(object(py_at(grid, py_to<int64>(y))), x, make_object(1));
        }
    }
    // Place multiple well-known long-lived patterns.
    object glider = make_object(list<object>{make_object(list<int64>{0, 1, 0}), make_object(list<int64>{0, 0, 1}), make_object(list<int64>{1, 1, 1})});
    object r_pentomino = make_object(list<object>{make_object(list<int64>{0, 1, 1}), make_object(list<int64>{1, 1, 0}), make_object(list<int64>{0, 1, 0})});
    object lwss = make_object(list<object>{make_object(list<int64>{0, 1, 1, 1, 1}), make_object(list<int64>{1, 0, 0, 0, 1}), make_object(list<int64>{0, 0, 0, 0, 1}), make_object(list<int64>{1, 0, 0, 1, 0})});
    
    for (int64 gy = 8; 18 > 0 ? gy < h - 8 : gy > h - 8; gy += 18) {
        for (int64 gx = 8; 22 > 0 ? gx < w - 8 : gx > w - 8; gx += 22) {
            int64 kind = (gx * 7 + gy * 11) % 3;
            int64 ph;
            if (kind == 0) {
                ph = py_len(glider);
                for (int64 py = 0; py < ph; ++py) {
                    int64 pw = py_len(object(py_at(glider, py_to<int64>(py))));
                    for (int64 px = 0; px < pw; ++px) {
                        if (int64(py_to<int64>(py_at(object(py_at(glider, py_to<int64>(py))), py_to<int64>(px)))) == 1)
                            py_set_at(object(py_at(grid, py_to<int64>((gy + py) % h))), (gx + px) % w, make_object(1));
                    }
                }
            } else {
                if (kind == 1) {
                    ph = py_len(r_pentomino);
                    for (int64 py = 0; py < ph; ++py) {
                        int64 pw = py_len(object(py_at(r_pentomino, py_to<int64>(py))));
                        for (int64 px = 0; px < pw; ++px) {
                            if (int64(py_to<int64>(py_at(object(py_at(r_pentomino, py_to<int64>(py))), py_to<int64>(px)))) == 1)
                                py_set_at(object(py_at(grid, py_to<int64>((gy + py) % h))), (gx + px) % w, make_object(1));
                        }
                    }
                } else {
                    ph = py_len(lwss);
                    for (int64 py = 0; py < ph; ++py) {
                        int64 pw = py_len(object(py_at(lwss, py_to<int64>(py))));
                        for (int64 px = 0; px < pw; ++px) {
                            if (int64(py_to<int64>(py_at(object(py_at(lwss, py_to<int64>(py))), py_to<int64>(px)))) == 1)
                                py_set_at(object(py_at(grid, py_to<int64>((gy + py) % h))), (gx + px) % w, make_object(1));
                        }
                    }
                }
            }
        }
    }
    object frames = make_object(list<object>{});
    for (int64 _ = 0; _ < steps; ++_) {
        py_append(frames, make_object(render(grid, w, h, cell)));
        grid = next_state(grid, w, h);
    }
    pytra::utils::gif::save_gif(out_path, w * cell, h * cell, frames, pytra::utils::gif::grayscale_palette(), int64(py_to<int64>(4)), int64(py_to<int64>(0)));
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_07_game_of_life_loop();
    return 0;
}
