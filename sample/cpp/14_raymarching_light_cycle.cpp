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

vector<uint8_t> palette()
{
    vector<uint8_t> p = py_bytearray();
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        long long r = static_cast<long long>((20 + (i * 0.9)));
        if ((r > 255))
        {
            r = 255;
        }
        long long g = static_cast<long long>((10 + (i * 0.7)));
        if ((g > 255))
        {
            g = 255;
        }
        long long b = static_cast<long long>((30 + i));
        if ((b > 255))
        {
            b = 255;
        }
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
    }
    return py_bytes(p);
}

long long scene(double x, double y, double light_x, double light_y)
{
    double x1 = (x + 0.45);
    double y1 = (y + 0.2);
    double x2 = (x - 0.35);
    double y2 = (y - 0.15);
    auto r1 = pycs::cpp_module::math::sqrt(((x1 * x1) + (y1 * y1)));
    auto r2 = pycs::cpp_module::math::sqrt(((x2 * x2) + (y2 * y2)));
    auto blob = (pycs::cpp_module::math::exp((((-7.0) * r1) * r1)) + pycs::cpp_module::math::exp((((-8.0) * r2) * r2)));
    auto lx = (x - light_x);
    auto ly = (y - light_y);
    auto l = pycs::cpp_module::math::sqrt(((lx * lx) + (ly * ly)));
    double lit = py_div(1.0, (1.0 + ((3.5 * l) * l)));
    long long v = static_cast<long long>((((255.0 * blob) * lit) * 5.0));
    if ((v < 0))
    {
        return 0;
    }
    if ((v > 255))
    {
        return 255;
    }
    return v;
}

void run_14_raymarching_light_cycle()
{
    long long w = 320;
    long long h = 240;
    long long frames_n = 84;
    string out_path = "sample/out/14_raymarching_light_cycle.gif";
    auto start = perf_counter();
    vector<vector<uint8_t>> frames = {};
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = frames_n;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto t = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (t < __pytra_range_stop_5) : (t > __pytra_range_stop_5); t += __pytra_range_step_6)
    {
        vector<uint8_t> frame = py_bytearray((w * h));
        double a = ((py_div(t, frames_n) * pycs::cpp_module::math::pi) * 2.0);
        double light_x = (0.75 * pycs::cpp_module::math::cos(a));
        double light_y = (0.55 * pycs::cpp_module::math::sin((a * 1.2)));
        long long i = 0;
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = h;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto y = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (y < __pytra_range_stop_8) : (y > __pytra_range_stop_8); y += __pytra_range_step_9)
        {
            double py = ((py_div(y, (h - 1)) * 2.0) - 1.0);
            auto __pytra_range_start_10 = 0;
            auto __pytra_range_stop_11 = w;
            auto __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
            for (auto x = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (x < __pytra_range_stop_11) : (x > __pytra_range_stop_11); x += __pytra_range_step_12)
            {
                double px = ((py_div(x, (w - 1)) * 2.0) - 1.0);
                frame[i] = scene(px, py, light_x, light_y);
                i = (i + 1);
            }
        }
        frames.push_back(py_bytes(frame));
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_14_raymarching_light_cycle();
    return 0;
}
