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

string render_frame(long long width, long long height, double cr, double ci, long long max_iter)
{
    string frame = py_bytearray((width * height));
    long long idx = 0;
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = height;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
    {
        double zy0 = ((-1.2) + (2.4 * py_div(y, (height - 1))));
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = width;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
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
            frame[idx] = static_cast<long long>(py_div((255.0 * i), max_iter));
            idx = (idx + 1);
        }
    }
    return py_bytes(frame);
}

void run_06_julia_parameter_sweep()
{
    long long width = 320;
    long long height = 240;
    long long frames_n = 50;
    long long max_iter = 120;
    string out_path = "sample/out/06_julia_parameter_sweep.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto __pytra_range_start_7 = 0;
    auto __pytra_range_stop_8 = frames_n;
    auto __pytra_range_step_9 = 1;
    if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (i < __pytra_range_stop_8) : (i > __pytra_range_stop_8); i += __pytra_range_step_9)
    {
        double t = py_div(i, frames_n);
        double cr = ((-0.8) + (0.32 * t));
        double ci = (0.156 + (0.22 * (0.5 - t)));
        frames.push_back(render_frame(width, height, cr, ci, max_iter));
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, pycs::cpp_module::gif::grayscale_palette(), 4, 0);
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
