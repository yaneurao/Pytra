#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
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

vector<uint8_t> color_palette()
{
    vector<uint8_t> p = py_bytearray();
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        auto r = i;
        long long g = ((i * 3) % 256);
        long long b = (255 - i);
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return py_bytes(p);
}

void run_11_lissajous_particles()
{
    long long w = 320;
    long long h = 240;
    long long frames_n = 360;
    long long particles = 48;
    string out_path = "sample/out/11_lissajous_particles.gif";
    auto start = perf_counter();
    vector<vector<uint8_t>> frames = {};
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = frames_n;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto t = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (t < __pytra_range_stop_5) : (t > __pytra_range_stop_5); t += __pytra_range_step_6)
    {
        vector<uint8_t> frame = py_bytearray((w * h));
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = particles;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto p = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (p < __pytra_range_stop_8) : (p > __pytra_range_stop_8); p += __pytra_range_step_9)
        {
            double phase = (p * 0.261799);
            long long x = static_cast<long long>(((w * 0.5) + ((w * 0.38) * pycs::cpp_module::math::sin(((0.11 * t) + (phase * 2.0))))));
            long long y = static_cast<long long>(((h * 0.5) + ((h * 0.38) * pycs::cpp_module::math::sin(((0.17 * t) + (phase * 3.0))))));
            long long color = (30 + ((p * 9) % 220));
            auto __pytra_range_start_10 = (-2);
            auto __pytra_range_stop_11 = 3;
            auto __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto dy = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dy < __pytra_range_stop_11) : (dy > __pytra_range_stop_11); dy += __pytra_range_step_12)
            {
                auto __pytra_range_start_13 = (-2);
                auto __pytra_range_stop_14 = 3;
                auto __pytra_range_step_15 = 1;
                if (__pytra_range_step_15 == 0) throw std::runtime_error("range() arg 3 must not be zero");
                for (auto dx = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (dx < __pytra_range_stop_14) : (dx > __pytra_range_stop_14); dx += __pytra_range_step_15)
                {
                    auto xx = (x + dx);
                    auto yy = (y + dy);
                    if (((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)))
                    {
                        auto d2 = ((dx * dx) + (dy * dy));
                        if ((d2 <= 4))
                        {
                            auto idx = ((yy * w) + xx);
                            long long v = (color - (d2 * 20));
                            if ((v < 0))
                            {
                                v = 0;
                            }
                            if ((v > frame[idx]))
                            {
                                frame[idx] = v;
                            }
                        }
                    }
                }
            }
        }
        frames.push_back(py_bytes(frame));
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_11_lissajous_particles();
    return 0;
}
