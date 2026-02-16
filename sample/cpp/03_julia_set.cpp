#include "cpp_module/gc.h"
#include "cpp_module/png.h"
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

string render_julia(long long width, long long height, long long max_iter, double cx, double cy)
{
    string pixels = py_bytearray();
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
            double zy = zy0;
            long long i = 0;
            while ((i < max_iter))
            {
                double zx2 = (zx * zx);
                double zy2 = (zy * zy);
                if (((zx2 + zy2) > 4.0))
                {
                    break;
                }
                zy = (((2.0 * zx) * zy) + cy);
                zx = ((zx2 - zy2) + cx);
                i = (i + 1);
            }
            long long r = 0;
            long long g = 0;
            long long b = 0;
            if ((i >= max_iter))
            {
                r = 0;
                g = 0;
                b = 0;
            }
            else
            {
                double t = py_div(i, max_iter);
                r = static_cast<long long>((255.0 * (0.2 + (0.8 * t))));
                g = static_cast<long long>((255.0 * (0.1 + (0.9 * (t * t)))));
                b = static_cast<long long>((255.0 * (1.0 - t)));
            }
            pixels.push_back(r);
            pixels.push_back(g);
            pixels.push_back(b);
        }
    }
    return pixels;
}

void run_julia()
{
    long long width = 1280;
    long long height = 720;
    long long max_iter = 520;
    string out_path = "sample/out/julia_03.png";
    double start = perf_counter();
    string pixels = render_julia(width, height, max_iter, (-0.8), 0.156);
    pycs::cpp_module::png::write_rgb_png(out_path, width, height, pixels);
    double elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_julia();
    return 0;
}
