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

string julia_palette()
{
    string palette = py_bytearray((256 * 3));
    palette[0] = 0;
    palette[1] = 0;
    palette[2] = 0;
    auto __pytra_range_start_1 = 1;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        double t = py_div((i - 1), 254.0);
        long long r = static_cast<long long>((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)));
        long long g = static_cast<long long>((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)));
        long long b = static_cast<long long>((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)));
        palette[((i * 3) + 0)] = r;
        palette[((i * 3) + 1)] = g;
        palette[((i * 3) + 2)] = b;
    }
    return py_bytes(palette);
}

string render_frame(long long width, long long height, double cr, double ci, long long max_iter, long long phase)
{
    string frame = py_bytearray((width * height));
    long long idx = 0;
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = height;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
    {
        double zy0 = ((-1.2) + (2.4 * py_div(y, (height - 1))));
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = width;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
        {
            double zx = ((-1.8) + (3.6 * py_div(x, (width - 1))));
            auto zy = zy0;
            long long i = 0;
            while ((i < max_iter))
            {
                auto zx2 = (zx * zx);
                auto zy2 = (zy * zy);
                if (((zx2 + zy2) > 4.0))
                {
                    break;
                }
                zy = (((2.0 * zx) * zy) + ci);
                zx = ((zx2 - zy2) + cr);
                i = (i + 1);
            }
            if ((i >= max_iter))
            {
                frame[idx] = 0;
            }
            else
            {
                long long color_index = (1 + ((py_floordiv((i * 224), max_iter) + phase) % 255));
                frame[idx] = color_index;
            }
            idx = (idx + 1);
        }
    }
    return py_bytes(frame);
}

void run_06_julia_parameter_sweep()
{
    long long width = 320;
    long long height = 240;
    long long frames_n = 72;
    long long max_iter = 180;
    string out_path = "sample/out/06_julia_parameter_sweep.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    double center_cr = (-0.745);
    double center_ci = 0.186;
    double radius_cr = 0.12;
    double radius_ci = 0.1;
    auto __pytra_range_start_10 = 0;
    auto __pytra_range_stop_11 = frames_n;
    auto __pytra_range_step_12 = 1;
    if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
    {
        double t = py_div(i, frames_n);
        double angle = ((2.0 * pycs::cpp_module::math::pi) * t);
        auto cr = (center_cr + (radius_cr * pycs::cpp_module::math::cos(angle)));
        auto ci = (center_ci + (radius_ci * pycs::cpp_module::math::sin(angle)));
        long long phase = ((i * 5) % 255);
        frames.push_back(render_frame(width, height, cr, ci, max_iter, phase));
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, julia_palette(), 8, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_06_julia_parameter_sweep();
    return 0;
}
