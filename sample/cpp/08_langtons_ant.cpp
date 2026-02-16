#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/py_runtime_modules.h"
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

string capture(const vector<vector<long long>>& grid, long long w, long long h)
{
    string frame = py_bytearray((w * h));
    long long i = 0;
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
            frame[i] = (grid[y][x] ? 255 : 0);
            i = (i + 1);
        }
    }
    return py_bytes(frame);
}

void run_08_langtons_ant()
{
    long long w = 240;
    long long h = 240;
    string out_path = "sample/out/08_langtons_ant.gif";
    auto start = perf_counter();
    vector<vector<long long>> grid = {};
    auto __pytra_range_start_7 = 0;
    auto __pytra_range_stop_8 = h;
    auto __pytra_range_step_9 = 1;
    if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto gy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (gy < __pytra_range_stop_8) : (gy > __pytra_range_stop_8); gy += __pytra_range_step_9)
    {
        vector<long long> row = {};
        auto __pytra_range_start_10 = 0;
        auto __pytra_range_stop_11 = w;
        auto __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto gx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (gx < __pytra_range_stop_11) : (gx > __pytra_range_stop_11); gx += __pytra_range_step_12)
        {
            row.push_back(0);
        }
        grid.push_back(row);
    }
    long long x = py_floordiv(w, 2);
    long long y = py_floordiv(h, 2);
    long long d = 0;
    long long steps_total = 180000;
    long long capture_every = 3000;
    vector<string> frames = {};
    auto __pytra_range_start_13 = 0;
    auto __pytra_range_stop_14 = steps_total;
    auto __pytra_range_step_15 = 1;
    if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
    {
        if ((grid[y][x] == 0))
        {
            d = ((d + 1) % 4);
            grid[y][x] = 1;
        }
        else
        {
            d = ((d + 3) % 4);
            grid[y][x] = 0;
        }
        if ((d == 0))
        {
            y = (((y - 1) + h) % h);
        }
        else
        {
            if ((d == 1))
            {
                x = ((x + 1) % w);
            }
            else
            {
                if ((d == 2))
                {
                    y = ((y + 1) % h);
                }
                else
                {
                    x = (((x - 1) + w) % w);
                }
            }
        }
        if (((i % capture_every) == 0))
        {
            frames.push_back(capture(grid, w, h));
        }
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 5, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_08_langtons_ant();
    return 0;
}
