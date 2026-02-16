#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
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

void run_10_plasma_effect()
{
    long long w = 320;
    long long h = 240;
    long long frames_n = 72;
    string out_path = "sample/out/10_plasma_effect.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = frames_n;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto t = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (t < __pytra_range_stop_2) : (t > __pytra_range_stop_2); t += __pytra_range_step_3)
    {
        string frame = py_bytearray((w * h));
        long long i = 0;
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = h;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            auto __pytra_range_start_7 = 0;
            auto __pytra_range_stop_8 = w;
            auto __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                long long dx = (x - 160);
                long long dy = (y - 120);
                auto v = (((pycs::cpp_module::math::sin(((x + (t * 2.0)) * 0.045)) + pycs::cpp_module::math::sin(((y - (t * 1.2)) * 0.05))) + pycs::cpp_module::math::sin((((x + y) + (t * 1.7)) * 0.03))) + pycs::cpp_module::math::sin(((pycs::cpp_module::math::sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))));
                long long c = static_cast<long long>(((v + 4.0) * py_div(255.0, 8.0)));
                if ((c < 0))
                {
                    c = 0;
                }
                if ((c > 255))
                {
                    c = 255;
                }
                frame[i] = c;
                i = (i + 1);
            }
        }
        frames.push_back(py_bytes(frame));
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_10_plasma_effect();
    return 0;
}
