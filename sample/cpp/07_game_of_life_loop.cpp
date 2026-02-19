#include "cpp_module/py_runtime.h"


// 07: Game of Life の進化をGIF出力するサンプル。

list<list<int64>> next_state(const list<list<int64>>& grid, int64 w, int64 h) {
    list<list<int64>> nxt = list<list<int64>>{};
    for (int64 y = 0; y < h; ++y) {
        list<int64> row = list<int64>{};
        for (int64 x = 0; x < w; ++x) {
            int64 cnt = 0;
            for (int64 dy = -1; dy < 2; ++dy) {
                for (int64 dx = -1; dx < 2; ++dx) {
                    if ((dx != 0) || (dy != 0)) {
                        int64 nx = (x + dx + w) % w;
                        int64 ny = (y + dy + h) % h;
                        cnt += grid[ny][nx];
                    }
                }
            }
            int64 alive = grid[y][x];
            if ((alive == 1) && ((cnt == 2) || (cnt == 3))) {
                row.append(1);
            } else {
                if ((alive == 0) && (cnt == 3))
                    row.append(1);
                else
                    row.append(0);
            }
        }
        nxt.append(row);
    }
    return nxt;
}

bytes render(const list<list<int64>>& grid, int64 w, int64 h, int64 cell) {
    int64 width = w * cell;
    int64 height = h * cell;
    bytearray frame = bytearray(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 v = (grid[y][x] ? 255 : 0);
            for (int64 yy = 0; yy < cell; ++yy) {
                int64 base = (y * cell + yy) * width + x * cell;
                for (int64 xx = 0; xx < cell; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return bytes(frame);
}

void run_07_game_of_life_loop() {
    int64 w = 144;
    int64 h = 108;
    int64 cell = 4;
    int64 steps = 210;
    str out_path = "sample/out/07_game_of_life_loop.gif";
    
    std::any start = make_object(perf_counter());
    list<list<int64>> grid = list<list<int64>>{};
    for (int64 _ = 0; _ < h; ++_) {
        list<int64> row = list<int64>{};
        for (int64 _ = 0; _ < w; ++_)
            row.append(0);
        grid.append(row);
    }
    
    // 疎なノイズを敷いて、全体が早期に固定化しにくい土台を作る。
    // 大きな整数リテラルを使わない式にして、各トランスパイラで同一に扱えるようにする。
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            int64 noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if (noise < 3)
                grid[y][x] = 1;
        }
    }
    
    // 代表的な長寿命パターンを複数配置する。
    list<list<int64>> glider = list<list<int64>>{list<int64>{0, 1, 0}, list<int64>{0, 0, 1}, list<int64>{1, 1, 1}};
    list<list<int64>> r_pentomino = list<list<int64>>{list<int64>{0, 1, 1}, list<int64>{1, 1, 0}, list<int64>{0, 1, 0}};
    list<list<int64>> lwss = list<list<int64>>{list<int64>{0, 1, 1, 1, 1}, list<int64>{1, 0, 0, 0, 1}, list<int64>{0, 0, 0, 0, 1}, list<int64>{1, 0, 0, 1, 0}};
    
    for (int64 gy = 8; 18 > 0 ? gy < h - 8 : gy > h - 8; gy += 18) {
        for (int64 gx = 8; 22 > 0 ? gx < w - 8 : gx > w - 8; gx += 22) {
            int64 kind = (gx * 7 + gy * 11) % 3;
            if (kind == 0) {
                int64 ph = py_len(glider);
                for (int64 py = 0; py < ph; ++py) {
                    int64 pw = py_len(glider[py]);
                    for (int64 px = 0; px < pw; ++px) {
                        if (glider[py][px] == 1)
                            grid[(gy + py) % h][(gx + px) % w] = 1;
                    }
                }
            } else {
                if (kind == 1) {
                    int64 ph = py_len(r_pentomino);
                    for (int64 py = 0; py < ph; ++py) {
                        int64 pw = py_len(r_pentomino[py]);
                        for (int64 px = 0; px < pw; ++px) {
                            if (r_pentomino[py][px] == 1)
                                grid[(gy + py) % h][(gx + px) % w] = 1;
                        }
                    }
                } else {
                    int64 ph = py_len(lwss);
                    for (int64 py = 0; py < ph; ++py) {
                        int64 pw = py_len(lwss[py]);
                        for (int64 px = 0; px < pw; ++px) {
                            if (lwss[py][px] == 1)
                                grid[(gy + py) % h][(gx + px) % w] = 1;
                        }
                    }
                }
            }
        }
    }
    
    list<bytes> frames = list<bytes>{};
    for (int64 _ = 0; _ < steps; ++_) {
        frames.append(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), 4, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_07_game_of_life_loop();
    return 0;
}
