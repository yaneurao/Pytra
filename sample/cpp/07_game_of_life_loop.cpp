#include "runtime/cpp/native/core/py_runtime.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"

#include "generated/built_in/io_ops.h"
#include "generated/built_in/sequence.h"
#include "generated/std/time.h"
#include "generated/utils/gif.h"

// 07: Sample that outputs Game of Life evolution as a GIF.

rc<list<list<int64>>> next_state(const rc<list<list<int64>>>& grid, int64 w, int64 h) {
    rc<list<list<int64>>> nxt = rc_list_from_value(list<list<int64>>{});
    for (int64 y = 0; y < h; ++y) {
        rc<list<int64>> row = rc_list_from_value(list<int64>{});
        for (int64 x = 0; x < w; ++x) {
            int64 cnt = 0;
            for (int64 dy = -(1); dy < 2; ++dy) {
                for (int64 dx = -(1); dx < 2; ++dx) {
                    if ((dx != 0) || (dy != 0)) {
                        int64 nx = (x + dx + w) % w;
                        int64 ny = (y + dy + h) % h;
                        cnt += py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>(ny)), py_to<int64>(nx));
                    }
                }
            }
            int64 alive = py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>(y)), py_to<int64>(x));
            if ((alive == 1) && ((cnt == 2) || (cnt == 3))) {
                py_list_append_mut(rc_list_ref(row), 1);
            } else if ((alive == 0) && (cnt == 3)) {
                py_list_append_mut(rc_list_ref(row), 1);
            } else {
                py_list_append_mut(rc_list_ref(row), 0);
            }
        }
        py_list_append_mut(rc_list_ref(nxt), rc_list_copy_value(row));
    }
    return nxt;
}

bytes render(const rc<list<list<int64>>>& grid, int64 w, int64 h, int64 cell) {
    int64 width = w * cell;
    int64 height = h * cell;
    bytearray frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>(y)), py_to<int64>(x)) ? 255 : 0);
            for (int64 yy = 0; yy < cell; ++yy) {
                int64 base = (y * cell + yy) * width + x * cell;
                for (int64 xx = 0; xx < cell; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return frame;
}

void run_07_game_of_life_loop() {
    int64 w = 144;
    int64 h = 108;
    int64 cell = 4;
    int64 steps = 105;
    str out_path = "sample/out/07_game_of_life_loop.gif";
    
    float64 start = pytra::std::time::perf_counter();
    rc<list<list<int64>>> grid = rc_list_from_value(list<list<int64>>(h, list<int64>(w, 0)));
    
    // Lay down sparse noise so the whole field is less likely to stabilize too early.
    // Avoid large integer literals so all transpilers handle the expression consistently.
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if (noise < 3)
                py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>(y)), py_to<int64>(x)) = 1;
        }
    }
    // Place multiple well-known long-lived patterns.
    rc<list<list<int64>>> glider = rc_list_from_value(list<list<int64>>{list<int64>{0, 1, 0}, list<int64>{0, 0, 1}, list<int64>{1, 1, 1}});
    rc<list<list<int64>>> r_pentomino = rc_list_from_value(list<list<int64>>{list<int64>{0, 1, 1}, list<int64>{1, 1, 0}, list<int64>{0, 1, 0}});
    rc<list<list<int64>>> lwss = rc_list_from_value(list<list<int64>>{list<int64>{0, 1, 1, 1, 1}, list<int64>{1, 0, 0, 0, 1}, list<int64>{0, 0, 0, 0, 1}, list<int64>{1, 0, 0, 1, 0}});
    
    for (int64 gy = 8; gy < h - 8; gy += 18) {
        for (int64 gx = 8; gx < w - 8; gx += 22) {
            int64 kind = (gx * 7 + gy * 11) % 3;
            int64 ph;
            int64 pw;
            if (kind == 0) {
                ph = (rc_list_ref(glider)).size();
                for (int64 py = 0; py < ph; ++py) {
                    pw = (py_list_at_ref(rc_list_ref(glider), py_to<int64>(py))).size();
                    for (int64 px = 0; px < pw; ++px) {
                        if (py_list_at_ref(py_list_at_ref(rc_list_ref(glider), py_to<int64>(py)), py_to<int64>(px)) == 1)
                            py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>((gy + py) % h)), py_to<int64>((gx + px) % w)) = 1;
                    }
                }
            } else if (kind == 1) {
                ph = (rc_list_ref(r_pentomino)).size();
                for (int64 py = 0; py < ph; ++py) {
                    pw = (py_list_at_ref(rc_list_ref(r_pentomino), py_to<int64>(py))).size();
                    for (int64 px = 0; px < pw; ++px) {
                        if (py_list_at_ref(py_list_at_ref(rc_list_ref(r_pentomino), py_to<int64>(py)), py_to<int64>(px)) == 1)
                            py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>((gy + py) % h)), py_to<int64>((gx + px) % w)) = 1;
                    }
                }
            } else {
                ph = (rc_list_ref(lwss)).size();
                for (int64 py = 0; py < ph; ++py) {
                    pw = (py_list_at_ref(rc_list_ref(lwss), py_to<int64>(py))).size();
                    for (int64 px = 0; px < pw; ++px) {
                        if (py_list_at_ref(py_list_at_ref(rc_list_ref(lwss), py_to<int64>(py)), py_to<int64>(px)) == 1)
                            py_list_at_ref(py_list_at_ref(rc_list_ref(grid), py_to<int64>((gy + py) % h)), py_to<int64>((gx + px) % w)) = 1;
                    }
                }
            }
        }
    }
    rc<list<bytes>> frames = rc_list_from_value(list<bytes>{});
    rc_list_ref(frames).reserve((steps <= 0) ? 0 : steps);
    for (int64 _ = 0; _ < steps; ++_) {
        py_list_append_mut(rc_list_ref(frames), render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    pytra::utils::gif::save_gif(out_path, w * cell, h * cell, rc_list_ref(frames), pytra::utils::gif::grayscale_palette(), 4, 0);
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
