#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
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

string capture(const vector<vector<long long>>& grid, long long w, long long h, long long scale)
{
    auto width = (w * scale);
    auto height = (h * scale);
    string frame = py_bytearray((width * height));
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = h;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
    {
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = w;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
        {
            auto v = ((grid[y][x] == 0) ? 255 : 40);
            auto __pytra_range_start_7 = 0;
            auto __pytra_range_stop_8 = scale;
            auto __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto yy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (yy < __pytra_range_stop_8) : (yy > __pytra_range_stop_8); yy += __pytra_range_step_9)
            {
                auto base = ((((y * scale) + yy) * width) + (x * scale));
                auto __pytra_range_start_10 = 0;
                auto __pytra_range_stop_11 = scale;
                auto __pytra_range_step_12 = 1;
                if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
                for (auto xx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (xx < __pytra_range_stop_11) : (xx > __pytra_range_stop_11); xx += __pytra_range_step_12)
                {
                    frame[(base + xx)] = v;
                }
            }
        }
    }
    return py_bytes(frame);
}

void run_13_maze_generation_steps()
{
    long long cell_w = 89;
    long long cell_h = 67;
    long long scale = 5;
    long long capture_every = 20;
    string out_path = "sample/out/13_maze_generation_steps.gif";
    auto start = perf_counter();
    vector<vector<long long>> grid = {};
    auto __pytra_range_start_13 = 0;
    auto __pytra_range_stop_14 = cell_h;
    auto __pytra_range_step_15 = 1;
    if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto _ = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (_ < __pytra_range_stop_14) : (_ > __pytra_range_stop_14); _ += __pytra_range_step_15)
    {
        vector<long long> row = {};
        auto __pytra_range_start_16 = 0;
        auto __pytra_range_stop_17 = cell_w;
        auto __pytra_range_step_18 = 1;
        if (__pytra_range_step_18 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto _ = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (_ < __pytra_range_stop_17) : (_ > __pytra_range_stop_17); _ += __pytra_range_step_18)
        {
            row.push_back(1);
        }
        grid.push_back(row);
    }
    vector<tuple<long long, long long>> stack = {std::make_tuple(1, 1)};
    grid[1][1] = 0;
    vector<tuple<long long, long long>> dirs = {std::make_tuple(2, 0), std::make_tuple((-2), 0), std::make_tuple(0, 2), std::make_tuple(0, (-2))};
    vector<string> frames = {};
    long long step = 0;
    while ((py_len(stack) > 0))
    {
        auto last_index = (py_len(stack) - 1);
        auto __pytra_tuple_19 = stack[last_index];
        auto x = std::get<0>(__pytra_tuple_19);
        auto y = std::get<1>(__pytra_tuple_19);
        vector<tuple<long long, long long, long long, long long>> candidates = {};
        auto __pytra_range_start_20 = 0;
        auto __pytra_range_stop_21 = 4;
        auto __pytra_range_step_22 = 1;
        if (__pytra_range_step_22 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto k = __pytra_range_start_20; (__pytra_range_step_22 > 0) ? (k < __pytra_range_stop_21) : (k > __pytra_range_stop_21); k += __pytra_range_step_22)
        {
            auto __pytra_tuple_23 = dirs[k];
            auto dx = std::get<0>(__pytra_tuple_23);
            auto dy = std::get<1>(__pytra_tuple_23);
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
        }
        if ((py_len(candidates) == 0))
        {
            py_pop(stack);
        }
        else
        {
            auto sel = candidates[((((x * 17) + (y * 29)) + (py_len(stack) * 13)) % py_len(candidates))];
            auto __pytra_tuple_24 = sel;
            auto nx = std::get<0>(__pytra_tuple_24);
            auto ny = std::get<1>(__pytra_tuple_24);
            auto wx = std::get<2>(__pytra_tuple_24);
            auto wy = std::get<3>(__pytra_tuple_24);
            grid[wy][wx] = 0;
            grid[ny][nx] = 0;
            stack.push_back(std::make_tuple(nx, ny));
        }
        if (((step % capture_every) == 0))
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
