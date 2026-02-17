#include "cpp_module/py_runtime.h"




list<list<int64>> next_state(list<list<int64>> grid, int64 w, int64 h) {
    list<int64> row;
    int64 cnt;
    int64 nx;
    int64 ny;
    int64 alive;
    
    list<list<int64>> nxt = list<list<int64>>{};
    for (int64 y = 0; y < h; ++y) {
        row = list<int64>{};
        for (int64 x = 0; x < w; ++x) {
            cnt = 0;
            for (int64 dy = -1; dy < 2; ++dy) {
                for (int64 dx = -1; dx < 2; ++dx) {
                    if ((dx != 0) || (dy != 0)) {
                        nx = (x + dx + w) % w;
                        ny = (y + dy + h) % h;
                        cnt += grid[ny][nx];
                    }
                }
            }
            alive = grid[y][x];
            if ((alive == 1) && ((cnt == 2) || (cnt == 3))) {
                row.push_back(1);
            } else {
                if ((alive == 0) && (cnt == 3))
                    row.push_back(1);
                else
                    row.push_back(0);
            }
        }
        nxt.push_back(row);
    }
    return nxt;
}

list<uint8> render(list<list<int64>> grid, int64 w, int64 h, int64 cell) {
    int64 v;
    int64 base;
    
    int64 width = w * cell;
    int64 height = h * cell;
    list<uint8> frame = list<uint8>(width * height);
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            v = (grid[y][x] ? 255 : 0);
            for (int64 yy = 0; yy < cell; ++yy) {
                base = (y * cell + yy) * width + x * cell;
                for (int64 xx = 0; xx < cell; ++xx)
                    frame[base + xx] = v;
            }
        }
    }
    return list<uint8>(frame);
}

void run_07_game_of_life_loop() {
    list<int64> row;
    int64 noise;
    int64 kind;
    int64 ph;
    int64 pw;
    list<list<int64>> grid;
    int64 _;
    int64 py;
    int64 px;
    
    int64 w = 144;
    int64 h = 108;
    int64 cell = 4;
    int64 steps = 210;
    str out_path = "sample/out/07_game_of_life_loop.gif";
    
    float64 start = perf_counter();
    grid = list<list<int64>>{};
    for (_ = 0; _ < h; ++_) {
        row = list<int64>{};
        for (_ = 0; _ < w; ++_)
            row.push_back(0);
        grid.push_back(row);
    }
    
    
    
    for (int64 y = 0; y < h; ++y) {
        for (int64 x = 0; x < w; ++x) {
            noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
            if (noise < 3)
                grid[y][x] = 1;
        }
    }
    
    
    list<list<int64>> glider = list<list<int64>>{list<int64>{0, 1, 0}, list<int64>{0, 0, 1}, list<int64>{1, 1, 1}};
    list<list<int64>> r_pentomino = list<list<int64>>{list<int64>{0, 1, 1}, list<int64>{1, 1, 0}, list<int64>{0, 1, 0}};
    list<list<int64>> lwss = list<list<int64>>{list<int64>{0, 1, 1, 1, 1}, list<int64>{1, 0, 0, 0, 1}, list<int64>{0, 0, 0, 0, 1}, list<int64>{1, 0, 0, 1, 0}};
    
    for (int64 gy = 8; gy < h - 8; gy += 18) {
        for (int64 gx = 8; gx < w - 8; gx += 22) {
            kind = (gx * 7 + gy * 11) % 3;
            if (kind == 0) {
                ph = py_len(glider);
                for (py = 0; py < ph; ++py) {
                    pw = py_len(glider[py]);
                    for (px = 0; px < pw; ++px) {
                        if (glider[py][px] == 1)
                            grid[(gy + py) % h][(gx + px) % w] = 1;
                    }
                }
            } else {
                if (kind == 1) {
                    ph = py_len(r_pentomino);
                    for (py = 0; py < ph; ++py) {
                        pw = py_len(r_pentomino[py]);
                        for (px = 0; px < pw; ++px) {
                            if (r_pentomino[py][px] == 1)
                                grid[(gy + py) % h][(gx + px) % w] = 1;
                        }
                    }
                } else {
                    ph = py_len(lwss);
                    for (py = 0; py < ph; ++py) {
                        pw = py_len(lwss[py]);
                        for (px = 0; px < pw; ++px) {
                            if (lwss[py][px] == 1)
                                grid[(gy + py) % h][(gx + px) % w] = 1;
                        }
                    }
                }
            }
        }
    }
    
    list<list<uint8>> frames = list<list<uint8>>{};
    for (_ = 0; _ < steps; ++_) {
        frames.push_back(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    
    save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), 4, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_07_game_of_life_loop();
    return 0;
}
