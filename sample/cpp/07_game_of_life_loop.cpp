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

vector<vector<long long>> next_state(const vector<vector<long long>>& grid, long long w, long long h)
{
    vector<vector<long long>> nxt = {};
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = h;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
    {
        vector<long long> row = {};
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = w;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
        {
            long long cnt = 0;
            auto __pytra_range_start_7 = (-1);
            auto __pytra_range_stop_8 = 2;
            auto __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto dy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (dy < __pytra_range_stop_8) : (dy > __pytra_range_stop_8); dy += __pytra_range_step_9)
            {
                auto __pytra_range_start_10 = (-1);
                auto __pytra_range_stop_11 = 2;
                auto __pytra_range_step_12 = 1;
                if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
                for (auto dx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dx < __pytra_range_stop_11) : (dx > __pytra_range_stop_11); dx += __pytra_range_step_12)
                {
                    if (((dx != 0) || (dy != 0)))
                    {
                        auto nx = (((x + dx) + w) % w);
                        auto ny = (((y + dy) + h) % h);
                        cnt = (cnt + grid[ny][nx]);
                    }
                }
            }
            auto alive = grid[y][x];
            if (((alive == 1) && ((cnt == 2) || (cnt == 3))))
            {
                row.push_back(1);
            }
            else
            {
                if (((alive == 0) && (cnt == 3)))
                {
                    row.push_back(1);
                }
                else
                {
                    row.push_back(0);
                }
            }
        }
        nxt.push_back(row);
    }
    return nxt;
}

string render(const vector<vector<long long>>& grid, long long w, long long h, long long cell)
{
    auto width = (w * cell);
    auto height = (h * cell);
    string frame = py_bytearray((width * height));
    auto __pytra_range_start_13 = 0;
    auto __pytra_range_stop_14 = h;
    auto __pytra_range_step_15 = 1;
    if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (y < __pytra_range_stop_14) : (y > __pytra_range_stop_14); y += __pytra_range_step_15)
    {
        auto __pytra_range_start_16 = 0;
        auto __pytra_range_stop_17 = w;
        auto __pytra_range_step_18 = 1;
        if (__pytra_range_step_18 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (x < __pytra_range_stop_17) : (x > __pytra_range_stop_17); x += __pytra_range_step_18)
        {
            auto v = (grid[y][x] ? 255 : 0);
            auto __pytra_range_start_19 = 0;
            auto __pytra_range_stop_20 = cell;
            auto __pytra_range_step_21 = 1;
            if (__pytra_range_step_21 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto yy = __pytra_range_start_19; (__pytra_range_step_21 > 0) ? (yy < __pytra_range_stop_20) : (yy > __pytra_range_stop_20); yy += __pytra_range_step_21)
            {
                auto base = ((((y * cell) + yy) * width) + (x * cell));
                auto __pytra_range_start_22 = 0;
                auto __pytra_range_stop_23 = cell;
                auto __pytra_range_step_24 = 1;
                if (__pytra_range_step_24 == 0) throw std::runtime_error("range() arg 3 must not be zero");
                for (auto xx = __pytra_range_start_22; (__pytra_range_step_24 > 0) ? (xx < __pytra_range_stop_23) : (xx > __pytra_range_stop_23); xx += __pytra_range_step_24)
                {
                    frame[(base + xx)] = v;
                }
            }
        }
    }
    return py_bytes(frame);
}

void run_07_game_of_life_loop()
{
    long long w = 144;
    long long h = 108;
    long long cell = 4;
    long long steps = 210;
    string out_path = "sample/out/07_game_of_life_loop.gif";
    auto start = perf_counter();
    vector<vector<long long>> grid = {};
    auto __pytra_range_start_25 = 0;
    auto __pytra_range_stop_26 = h;
    auto __pytra_range_step_27 = 1;
    if (__pytra_range_step_27 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_25; (__pytra_range_step_27 > 0) ? (y < __pytra_range_stop_26) : (y > __pytra_range_stop_26); y += __pytra_range_step_27)
    {
        vector<long long> row = {};
        auto __pytra_range_start_28 = 0;
        auto __pytra_range_stop_29 = w;
        auto __pytra_range_step_30 = 1;
        if (__pytra_range_step_30 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_28; (__pytra_range_step_30 > 0) ? (x < __pytra_range_stop_29) : (x > __pytra_range_stop_29); x += __pytra_range_step_30)
        {
            row.push_back(((((((x * 17) + (y * 31)) + 13) % 11) < 3) ? 1 : 0));
        }
        grid.push_back(row);
    }
    vector<string> frames = {};
    auto __pytra_range_start_31 = 0;
    auto __pytra_range_stop_32 = steps;
    auto __pytra_range_step_33 = 1;
    if (__pytra_range_step_33 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto _ = __pytra_range_start_31; (__pytra_range_step_33 > 0) ? (_ < __pytra_range_stop_32) : (_ > __pytra_range_stop_32); _ += __pytra_range_step_33)
    {
        frames.push_back(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
    }
    pycs::cpp_module::gif::save_gif(out_path, (w * cell), (h * cell), frames, pycs::cpp_module::gif::grayscale_palette(), 4, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_07_game_of_life_loop();
    return 0;
}
