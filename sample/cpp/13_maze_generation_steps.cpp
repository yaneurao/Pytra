#include "cpp_module/py_runtime.h"

// 13: DFS迷路生成の進行状況をGIF出力するサンプル。

bytearray capture(const list<list<int64>>& grid, int64 w, int64 h, int64 scale) {
    int64 width = w * scale;
    int64 height = h * scale;
    auto frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (grid[y][x] == 0 ? 255 : 40);
            for (int64 yy = 0; yy < scale; ++yy) {
                int64 base = (y * scale + yy) * width + x * scale;
                for (int64 xx = 0; xx < scale; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return bytearray(frame);
}

void run_13_maze_generation_steps() {
    // 実行時間を十分に確保するため、迷路サイズと描画解像度を上げる。
    int64 cell_w = 89;
    int64 cell_h = 67;
    int64 scale = 5;
    int64 capture_every = 20;
    str out_path = "sample/out/13_maze_generation_steps.gif";
    
    auto start = perf_counter();
    list<list<int64>> grid = [&]() -> list<list<int64>> {     list<list<int64>> __out;     for (int64 _ = 0; (_ < cell_h); _ += (1)) {         __out.append(py_repeat(list<int64>{1}, cell_w));     }     return __out; }();
    list<std::tuple<int64, int64>> stack = list<std::tuple<int64, int64>>{std::make_tuple(1, 1)};
    grid[1][1] = 0;
    
    list<std::tuple<int64, int64>> dirs = list<std::tuple<int64, int64>>{std::make_tuple(2, 0), std::make_tuple(-2, 0), std::make_tuple(0, 2), std::make_tuple(0, -2)};
    list<bytearray> frames = list<bytearray>{};
    int64 step = 0;
    
    while (py_len(stack) != 0) {
        auto __tuple_1 = py_at(stack, -1);
        auto x = std::get<0>(__tuple_1);
        auto y = std::get<1>(__tuple_1);
        list<std::tuple<int64, int64, int64, int64>> candidates = list<std::tuple<int64, int64, int64, int64>>{};
        for (int64 k = 0; k < 4; ++k) {
            auto __tuple_2 = dirs[k];
            auto dx = std::get<0>(__tuple_2);
            auto dy = std::get<1>(__tuple_2);
            auto nx = x + dx;
            auto ny = y + dy;
            if ((nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (grid[ny][nx] == 1)) {
                if (dx == 2) {
                    candidates.append(std::make_tuple(nx, ny, x + 1, y));
                } else {
                    if (dx == -2) {
                        candidates.append(std::make_tuple(nx, ny, x - 1, y));
                    } else {
                        if (dy == 2)
                            candidates.append(std::make_tuple(nx, ny, x, y + 1));
                        else
                            candidates.append(std::make_tuple(nx, ny, x, y - 1));
                    }
                }
            }
        }
        
        if (py_len(candidates) == 0) {
            py_pop(stack);
        } else {
            auto sel = candidates[(x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates)];
            auto __tuple_3 = sel;
            auto nx = std::get<0>(__tuple_3);
            auto ny = std::get<1>(__tuple_3);
            auto wx = std::get<2>(__tuple_3);
            auto wy = std::get<3>(__tuple_3);
            grid[wy][wx] = 0;
            grid[ny][nx] = 0;
            stack.append(std::make_tuple(nx, ny));
        }
        
        if (step % capture_every == 0)
            frames.append(capture(grid, cell_w, cell_h, scale));
        step++;
    }
    
    frames.append(capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette(), 4, 0);
    auto elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_13_maze_generation_steps();
    return 0;
}
