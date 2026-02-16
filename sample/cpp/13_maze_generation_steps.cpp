#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/py_runtime_modules.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

string capture(const vector<vector<int>>& grid, int w, int h, int scale)
{
    auto width = (w * scale);
    auto height = (h * scale);
    auto frame = string(static_cast<size_t>((width * height)), '\0');
    auto y = 0;
    while ((y < h))
    {
        auto x = 0;
        while ((x < w))
        {
            auto v = ((grid[y][x] == 0) ? 255 : 40);
            auto yy = 0;
            while ((yy < scale))
            {
                auto base = ((((y * scale) + yy) * width) + (x * scale));
                auto xx = 0;
                while ((xx < scale))
                {
                    // unsupported assignment
                    xx = (xx + 1);
                }
                yy = (yy + 1);
            }
            x = (x + 1);
        }
        y = (y + 1);
    }
    return frame;
}

void run_13_maze_generation_steps()
{
    auto cell_w = 61;
    auto cell_h = 45;
    auto scale = 4;
    auto out_path = "sample/out/13_maze_generation_steps.gif";
    auto start = perf_counter();
    vector<vector<int>> grid = {};
    auto gy = 0;
    while ((gy < cell_h))
    {
        vector<int> row = {};
        auto gx = 0;
        while ((gx < cell_w))
        {
            row.push_back(1);
            gx = (gx + 1);
        }
        grid.push_back(row);
        gy = (gy + 1);
    }
    vector<tuple<int, int>> stack = {std::make_tuple(1, 1)};
    // unsupported assignment
    vector<tuple<int, int>> dirs = {std::make_tuple(2, 0), std::make_tuple((-2), 0), std::make_tuple(0, 2), std::make_tuple(0, (-2))};
    vector<string> frames = {};
    auto step = 0;
    while ((py_len(stack) > 0))
    {
        auto _tmp_tuple = stack[(-1)];
        auto x = std::get<0>(_tmp_tuple);
        auto y = std::get<1>(_tmp_tuple);
        vector<tuple<int, int, int, int>> candidates = {};
        auto k = 0;
        while ((k < 4))
        {
            auto _tmp_tuple = dirs[k];
            auto dx = std::get<0>(_tmp_tuple);
            auto dy = std::get<1>(_tmp_tuple);
            auto nx = (x + dx);
            auto ny = (y + dy);
            if (((nx >= 1) && (nx < (cell_w - 1)) && (ny >= 1) && (ny < (cell_h - 1)) && (grid[ny][nx] == 1)))
            {
                if ((dx == 2))
                {
                    candidates.push_back(std::make_tuple(nx, ny, (x + 1), y));
                }
                else
                {
                    if ((dx == (-2)))
                    {
                        candidates.push_back(std::make_tuple(nx, ny, (x - 1), y));
                    }
                    else
                    {
                        if ((dy == 2))
                        {
                            candidates.push_back(std::make_tuple(nx, ny, x, (y + 1)));
                        }
                        else
                        {
                            candidates.push_back(std::make_tuple(nx, ny, x, (y - 1)));
                        }
                    }
                }
            }
            k = (k + 1);
        }
        if ((py_len(candidates) == 0))
        {
            stack.pop_back();
        }
        else
        {
            auto sel = candidates[((((x * 17) + (y * 29)) + (py_len(stack) * 13)) % py_len(candidates))];
            auto _tmp_tuple = sel;
            auto nx = std::get<0>(_tmp_tuple);
            auto ny = std::get<1>(_tmp_tuple);
            auto wx = std::get<2>(_tmp_tuple);
            auto wy = std::get<3>(_tmp_tuple);
            // unsupported assignment
            // unsupported assignment
            stack.push_back(std::make_tuple(nx, ny));
        }
        if (((step % 25) == 0))
        {
            frames.push_back(capture(grid, cell_w, cell_h, scale));
        }
        step = (step + 1);
    }
    frames.push_back(capture(grid, cell_w, cell_h, scale));
    pycs::cpp_module::gif::save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, pycs::cpp_module::gif::grayscale_palette(), 4, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_13_maze_generation_steps();
    return 0;
}
