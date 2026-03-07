#include "runtime/cpp/core/py_runtime.h"

#include "pytra/built_in/sequence.h"
#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 13: Sample that outputs DFS maze-generation progress as a GIF.

bytes capture(const rc<list<list<int64>>>& grid, int64 w, int64 h, int64 scale) {
    int64 width = w * scale;
    int64 height = h * scale;
    bytearray frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (py_at(py_at(grid, py_to<int64>(y)), py_to<int64>(x)) == 0 ? 255 : 40);
            for (int64 yy = 0; yy < scale; ++yy) {
                int64 base = (y * scale + yy) * width + x * scale;
                for (int64 xx = 0; xx < scale; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return frame;
}

void run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    int64 cell_w = 89;
    int64 cell_h = 67;
    int64 scale = 5;
    int64 capture_every = 20;
    str out_path = "sample/out/13_maze_generation_steps.gif";
    
    float64 start = pytra::std::time::perf_counter();
    rc<list<list<int64>>> grid = rc_list_from_value(list<list<int64>>(cell_h, list<int64>(cell_w, 1)));
    rc<list<::std::tuple<int64, int64>>> stack = rc_list_from_value(list<::std::tuple<int64, int64>>{::std::make_tuple(1, 1)});
    py_list_at_ref(py_at(grid, py_to<int64>(1)), py_to<int64>(1)) = 0;
    
    rc<list<::std::tuple<int64, int64>>> dirs = rc_list_from_value(list<::std::tuple<int64, int64>>{::std::make_tuple(2, 0), ::std::make_tuple(-(2), 0), ::std::make_tuple(0, 2), ::std::make_tuple(0, -(2))});
    rc<list<bytes>> frames = rc_list_from_value(list<bytes>{});
    int64 step = 0;
    
    while (!((rc_list_ref(stack)).empty())) {
        auto [x, y] = py_at(stack, py_to<int64>(-(1)));
        rc<list<::std::tuple<int64, int64, int64, int64>>> candidates = rc_list_from_value(list<::std::tuple<int64, int64, int64, int64>>{});
        for (int64 k = 0; k < 4; ++k) {
            auto [dx, dy] = py_at(dirs, py_to<int64>(k));
            int64 nx = x + dx;
            int64 ny = y + dy;
            if ((nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (py_at(py_at(grid, py_to<int64>(ny)), py_to<int64>(nx)) == 1)) {
                if (dx == 2) {
                    py_append(candidates, ::std::make_tuple(nx, ny, x + 1, y));
                } else if (dx == -(2)) {
                    py_append(candidates, ::std::make_tuple(nx, ny, x - 1, y));
                } else if (dy == 2) {
                    py_append(candidates, ::std::make_tuple(nx, ny, x, y + 1));
                } else {
                    py_append(candidates, ::std::make_tuple(nx, ny, x, y - 1));
                }
            }
        }
        if ((rc_list_ref(candidates)).empty()) {
            py_pop(stack);
        } else {
            auto __idx_3 = (x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates);
            ::std::tuple<int64, int64, int64, int64> sel = py_at(candidates, py_to<int64>(__idx_3));
            auto [nx, ny, wx, wy] = sel;
            py_list_at_ref(py_at(grid, py_to<int64>(wy)), py_to<int64>(wx)) = 0;
            py_list_at_ref(py_at(grid, py_to<int64>(ny)), py_to<int64>(nx)) = 0;
            py_append(stack, ::std::make_tuple(nx, ny));
        }
        if (step % capture_every == 0)
            py_append(frames, capture(grid, cell_w, cell_h, scale));
        step++;
    }
    py_append(frames, capture(grid, cell_w, cell_h, scale));
    pytra::utils::gif::save_gif(out_path, cell_w * scale, cell_h * scale, rc_list_ref(frames), pytra::utils::gif::grayscale_palette(), 4, 0);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_13_maze_generation_steps();
    return 0;
}
