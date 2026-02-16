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

string fire_palette()
{
    string p = py_bytearray();
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        long long r = 0;
        long long g = 0;
        long long b = 0;
        if ((i < 85))
        {
            r = (i * 3);
            g = 0;
            b = 0;
        }
        else
        {
            if ((i < 170))
            {
                r = 255;
                g = ((i - 85) * 3);
                b = 0;
            }
            else
            {
                r = 255;
                g = 255;
                b = ((i - 170) * 3);
            }
        }
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return py_bytes(p);
}

void run_09_fire_simulation()
{
    long long w = 220;
    long long h = 140;
    long long steps = 110;
    string out_path = "sample/out/09_fire_simulation.gif";
    auto start = perf_counter();
    vector<vector<long long>> heat = {};
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = h;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto _ = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (_ < __pytra_range_stop_5) : (_ > __pytra_range_stop_5); _ += __pytra_range_step_6)
    {
        vector<long long> row = {};
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = w;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto _ = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (_ < __pytra_range_stop_8) : (_ > __pytra_range_stop_8); _ += __pytra_range_step_9)
        {
            row.push_back(0);
        }
        heat.push_back(row);
    }
    vector<string> frames = {};
    auto __pytra_range_start_10 = 0;
    auto __pytra_range_stop_11 = steps;
    auto __pytra_range_step_12 = 1;
    if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto t = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (t < __pytra_range_stop_11) : (t > __pytra_range_stop_11); t += __pytra_range_step_12)
    {
        auto __pytra_range_start_13 = 0;
        auto __pytra_range_stop_14 = w;
        auto __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (x < __pytra_range_stop_14) : (x > __pytra_range_stop_14); x += __pytra_range_step_15)
        {
            long long val = (170 + (((x * 13) + (t * 17)) % 86));
            heat[(h - 1)][x] = val;
        }
        auto __pytra_range_start_16 = 1;
        auto __pytra_range_stop_17 = h;
        auto __pytra_range_step_18 = 1;
        if (__pytra_range_step_18 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto y = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (y < __pytra_range_stop_17) : (y > __pytra_range_stop_17); y += __pytra_range_step_18)
        {
            auto __pytra_range_start_19 = 0;
            auto __pytra_range_stop_20 = w;
            auto __pytra_range_step_21 = 1;
            if (__pytra_range_step_21 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto x = __pytra_range_start_19; (__pytra_range_step_21 > 0) ? (x < __pytra_range_stop_20) : (x > __pytra_range_stop_20); x += __pytra_range_step_21)
            {
                auto a = heat[y][x];
                auto b = heat[y][(((x - 1) + w) % w)];
                auto c = heat[y][((x + 1) % w)];
                auto d = heat[((y + 1) % h)][x];
                auto v = py_floordiv((((a + b) + c) + d), 4);
                auto cool = (1 + (((x + y) + t) % 3));
                auto nv = (v - cool);
                heat[(y - 1)][x] = ((nv > 0) ? nv : 0);
            }
        }
        string frame = py_bytearray((w * h));
        long long i = 0;
        auto __pytra_range_start_22 = 0;
        auto __pytra_range_stop_23 = h;
        auto __pytra_range_step_24 = 1;
        if (__pytra_range_step_24 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto yy = __pytra_range_start_22; (__pytra_range_step_24 > 0) ? (yy < __pytra_range_stop_23) : (yy > __pytra_range_stop_23); yy += __pytra_range_step_24)
        {
            auto __pytra_range_start_25 = 0;
            auto __pytra_range_stop_26 = w;
            auto __pytra_range_step_27 = 1;
            if (__pytra_range_step_27 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto xx = __pytra_range_start_25; (__pytra_range_step_27 > 0) ? (xx < __pytra_range_stop_26) : (xx > __pytra_range_stop_26); xx += __pytra_range_step_27)
            {
                frame[i] = heat[yy][xx];
                i = (i + 1);
            }
        }
        frames.push_back(py_bytes(frame));
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_09_fire_simulation();
    return 0;
}
