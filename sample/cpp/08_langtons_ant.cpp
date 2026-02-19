#include "cpp_module/py_runtime.h"


// 08: ラングトンのアリの軌跡をGIF出力するサンプル。

bytes capture(const list<list<int64>>& grid, int64 w, int64 h) {
    bytearray frame = bytearray(w * h);
    int64 i = 0;
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            frame[i] = (grid[y][x] ? 255 : 0);
            i++;
        }
    }
    return bytes(frame);
}

void run_08_langtons_ant() {
    int64 w = 420;
    int64 h = 420;
    str out_path = "sample/out/08_langtons_ant.gif";
    
    std::any start = make_object(perf_counter());
    
    list<list<int64>> grid = list<list<int64>>{};
    for (int64 gy = 0; gy < h; ++gy) {
        list<int64> row = list<int64>{};
        for (int64 gx = 0; gx < w; ++gx)
            row.append(0);
        grid.append(row);
    }
    int64 x = py_floordiv(w, 2);
    int64 y = py_floordiv(h, 2);
    int64 d = 0;
    
    int64 steps_total = 600000;
    int64 capture_every = 3000;
    list<bytes> frames = list<bytes>{};
    
    for (int64 i = 0; i < steps_total; ++i) {
        if (grid[y][x] == 0) {
            d = (d + 1) % 4;
            grid[y][x] = 1;
        } else {
            d = (d + 3) % 4;
            grid[y][x] = 0;
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
            frames.append(capture(grid, w, h));
    }
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, w, h, frames, grayscale_palette(), 5, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_08_langtons_ant();
    return 0;
}
