#include "cpp_module/py_runtime.h"




list<uint8> capture(list<list<int64>> grid, int64 w, int64 h, int64 scale) {
    int64 v;
    int64 base;
    
    int64 width = w * scale;
    int64 height = h * scale;
    list<uint8> frame = list<uint8>(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            v = (grid[y][x] == 0 ? 255 : 40);
            for (int64 yy = 0; yy < scale; ++yy) {
                base = (y * scale + yy) * width + x * scale;
                for (int64 xx = 0; xx < scale; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return list<uint8>(frame);
}

void run_13_maze_generation_steps() {
    int64 x;
    int64 y;
    list<std::tuple<int64, int64, int64, int64>> candidates;
    int64 dx;
    int64 dy;
    int64 nx;
    int64 ny;
    std::tuple<int64, int64, int64, int64> sel;
    int64 wx;
    int64 wy;
    
    int64 cell_w = 89;
    int64 cell_h = 67;
    int64 scale = 5;
    int64 capture_every = 20;
    str out_path = "sample/out/13_maze_generation_steps.gif";
    
    float64 start = perf_counter();
    list<list<int64>> grid = [&]() -> list<list<int64>> {     list<list<int64>> __out;     for (int64 _ = 0; (_ < cell_h); _ += (1)) {         __out.push_back(py_repeat(list<int64>{1}, cell_w));     }     return __out; }();
    list<std::tuple<int64, int64>> stack = list<std::tuple<int64, int64>>{std::make_tuple(1, 1)};
    grid[1][1] = 0;
    
    list<std::tuple<int64, int64>> dirs = list<std::tuple<int64, int64>>{std::make_tuple(2, 0), std::make_tuple(-2, 0), std::make_tuple(0, 2), std::make_tuple(0, -2)};
    list<list<uint8>> frames = list<list<uint8>>{};
    int64 step = 0;
    
    while ((py_len(stack) != 0)) {
        auto __tuple_1 = py_at(stack, -1);
        x = std::get<0>(__tuple_1);
        y = std::get<1>(__tuple_1);
        candidates = list<std::tuple<int64, int64, int64, int64>>{};
        for (int64 k = 0; k < 4; ++k) {
            auto __tuple_2 = dirs[k];
            dx = std::get<0>(__tuple_2);
            dy = std::get<1>(__tuple_2);
            nx = x + dx;
            ny = y + dy;
            if (nx >= 1 && nx < cell_w - 1 && ny >= 1 && ny < cell_h - 1 && grid[ny][nx] == 1) {
                if (dx == 2) {
                    candidates.push_back(std::make_tuple(nx, ny, x + 1, y));
                } else {
                    if (dx == -2) {
                        candidates.push_back(std::make_tuple(nx, ny, x - 1, y));
                    } else {
                        if (dy == 2)
                            candidates.push_back(std::make_tuple(nx, ny, x, y + 1));
                        else
                            candidates.push_back(std::make_tuple(nx, ny, x, y - 1));
                    }
                }
            }
        }
        
        if (py_len(candidates) == 0) {
            py_pop(stack);
        } else {
            sel = candidates[(x * 17 + y * 29 + py_len(stack) * 13) % py_len(candidates)];
            auto __tuple_3 = sel;
            nx = std::get<0>(__tuple_3);
            ny = std::get<1>(__tuple_3);
            wx = std::get<2>(__tuple_3);
            wy = std::get<3>(__tuple_3);
            grid[wy][wx] = 0;
            grid[ny][nx] = 0;
            stack.push_back(std::make_tuple(nx, ny));
        }
        
        if (step % capture_every == 0)
            frames.push_back(capture(grid, cell_w, cell_h, scale));
        step++;
    }
    
    frames.push_back(capture(grid, cell_w, cell_h, scale));
    save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette(), 4, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_13_maze_generation_steps();
    return 0;
}
