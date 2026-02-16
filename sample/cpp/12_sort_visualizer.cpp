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

string render(const vector<long long>& values, long long w, long long h)
{
    string frame = py_bytearray((w * h));
    size_t n = py_len(values);
    double bar_w = py_div(w, n);
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = n;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        long long x0 = static_cast<long long>((i * bar_w));
        long long x1 = static_cast<long long>(((i + 1) * bar_w));
        if ((x1 <= x0))
        {
            x1 = (x0 + 1);
        }
        long long bh = static_cast<long long>((py_div(values[i], n) * h));
        auto y = (h - bh);
        auto __pytra_range_start_4 = y;
        auto __pytra_range_stop_5 = h;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            auto __pytra_range_start_7 = x0;
            auto __pytra_range_stop_8 = x1;
            auto __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                frame[((y * w) + x)] = 255;
            }
        }
    }
    return py_bytes(frame);
}

void run_12_sort_visualizer()
{
    long long w = 320;
    long long h = 180;
    long long n = 72;
    string out_path = "sample/out/12_sort_visualizer.gif";
    auto start = perf_counter();
    vector<long long> values = {};
    auto __pytra_range_start_10 = 0;
    auto __pytra_range_stop_11 = n;
    auto __pytra_range_step_12 = 1;
    if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
    {
        values.push_back((((i * 37) + 19) % n));
    }
    vector<string> frames = {render(values, w, h)};
    long long op = 0;
    auto __pytra_range_start_13 = 0;
    auto __pytra_range_stop_14 = n;
    auto __pytra_range_step_15 = 1;
    if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
    {
        bool swapped = false;
        auto __pytra_range_start_16 = 0;
        auto __pytra_range_stop_17 = ((n - i) - 1);
        auto __pytra_range_step_18 = 1;
        if (__pytra_range_step_18 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto j = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (j < __pytra_range_stop_17) : (j > __pytra_range_stop_17); j += __pytra_range_step_18)
        {
            if ((values[j] > values[(j + 1)]))
            {
                auto tmp = values[j];
                values[j] = values[(j + 1)];
                values[(j + 1)] = tmp;
                swapped = true;
            }
            if (((op % 8) == 0))
            {
                frames.push_back(render(values, w, h));
            }
            op = (op + 1);
        }
        if ((!swapped))
        {
            break;
        }
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_12_sort_visualizer();
    return 0;
}
