#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"
#include "pytra/utils/gif.h"

// 13: Sample that outputs DFS maze-generation progress as a GIF.

bytes capture(const object& grid, int64 w, int64 h, int64 scale) {
    int64 width = w * scale;
    int64 height = h * scale;
    bytearray frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(y))), py_to<int64>(x)))) == 0 ? 255 : 40);
            for (int64 yy = 0; yy < scale; ++yy) {
                int64 base = (y * scale + yy) * width + x * scale;
                for (int64 xx = 0; xx < scale; ++xx) {
                    frame[base + xx] = v;
                }
            }
        }
    }
    return bytes(frame);
}

void run_13_maze_generation_steps() {
    // Increase maze size and render resolution to ensure sufficient runtime.
    int64 cell_w = 89;
    int64 cell_h = 67;
    int64 scale = 5;
    int64 capture_every = 20;
    str out_path = "sample/out/13_maze_generation_steps.gif";
    
    float64 start = pytra::std::time::perf_counter();
    object grid = [&]() -> object {     list<object> __out;     for (int64 _ = 0; (_ < cell_h); _ += (1)) {         __out.append(make_object(py_repeat(list<int64>(make_object(list<int64>{1})), cell_w)));     }     return make_object(__out); }();
    object stack = make_object(list<::std::tuple<int64, int64>>{::std::make_tuple(1, 1)});
    py_set_at(object(py_at(grid, py_to<int64>(1))), 1, make_object(0));
    
    object dirs = make_object(list<::std::tuple<int64, int64>>{::std::make_tuple(2, 0), ::std::make_tuple(-2, 0), ::std::make_tuple(0, 2), ::std::make_tuple(0, -2)});
    object frames = make_object(list<object>{});
    int64 step = 0;
    
    while (py_len(stack) != 0) {
        auto __tuple_2 = ::std::make_tuple(int64(py_to<int64>(py_at(py_at(stack, py_to<int64>(-1)), 0))), int64(py_to<int64>(py_at(py_at(stack, py_to<int64>(-1)), 1))));
        int64 x = ::std::get<0>(__tuple_2);
        int64 y = ::std::get<1>(__tuple_2);
        object candidates = make_object(list<object>{});
        for (int64 k = 0; k < 4; ++k) {
            auto __tuple_3 = ::std::make_tuple(int64(py_to<int64>(py_at(py_at(dirs, py_to<int64>(k)), 0))), int64(py_to<int64>(py_at(py_at(dirs, py_to<int64>(k)), 1))));
            int64 dx = ::std::get<0>(__tuple_3);
            int64 dy = ::std::get<1>(__tuple_3);
            int64 nx = x + dx;
            int64 ny = y + dy;
            if ((nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (int64(py_to<int64>(py_at(object(py_at(grid, py_to<int64>(ny))), py_to<int64>(nx)))) == 1)) {
                if (dx == 2) {
                    py_append(candidates, make_object(::std::make_tuple(nx, ny, x + 1, y)));
                } else {
                    if (dx == -2) {
                        py_append(candidates, make_object(::std::make_tuple(nx, ny, x - 1, y)));
                    } else {
                        if (dy == 2)
                            py_append(candidates, make_object(::std::make_tuple(nx, ny, x, y + 1)));
                        else
                            py_append(candidates, make_object(::std::make_tuple(nx, ny, x, y - 1)));
                    }
                }
            }
        }
        if (py_len(candidates) == 0) {
            py_pop(stack);
        } else {
            ::std::tuple<int64, int64, int64, int64> sel = ::std::make_tuple(int64(py_to<int64>(py_at(py_at(candidates, py_to<int64>((x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates))), 0))), int64(py_to<int64>(py_at(py_at(candidates, py_to<int64>((x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates))), 1))), int64(py_to<int64>(py_at(py_at(candidates, py_to<int64>((x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates))), 2))), int64(py_to<int64>(py_at(py_at(candidates, py_to<int64>((x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates))), 3))));
            auto __tuple_4 = sel;
            int64 nx = ::std::get<0>(__tuple_4);
            int64 ny = ::std::get<1>(__tuple_4);
            int64 wx = ::std::get<2>(__tuple_4);
            int64 wy = ::std::get<3>(__tuple_4);
            py_set_at(object(py_at(grid, py_to<int64>(wy))), wx, make_object(0));
            py_set_at(object(py_at(grid, py_to<int64>(ny))), nx, make_object(0));
            py_append(stack, make_object(::std::make_tuple(nx, ny)));
        }
        if (step % capture_every == 0)
            py_append(frames, make_object(capture(grid, cell_w, cell_h, scale)));
        step++;
    }
    py_append(frames, make_object(capture(grid, cell_w, cell_h, scale)));
    pytra::utils::gif::save_gif(out_path, cell_w * scale, cell_h * scale, frames, pytra::utils::gif::grayscale_palette(), 4, 0);
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
