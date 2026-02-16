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

long long escape_count(double cx, double cy, long long max_iter)
{
    double x = 0.0;
    double y = 0.0;
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = max_iter;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        double x2 = (x * x);
        double y2 = (y * y);
        if (((x2 + y2) > 4.0))
        {
            return i;
        }
        y = (((2.0 * x) * y) + cy);
        x = ((x2 - y2) + cx);
    }
    return max_iter;
}

tuple<long long, long long, long long> color_map(long long iter_count, long long max_iter)
{
    if ((iter_count >= max_iter))
    {
        return std::make_tuple(0, 0, 0);
    }
    double t = py_div(iter_count, max_iter);
    long long r = static_cast<long long>((255.0 * (t * t)));
    long long g = static_cast<long long>((255.0 * t));
    long long b = static_cast<long long>((255.0 * (1.0 - t)));
    return std::make_tuple(r, g, b);
}

string render_mandelbrot(long long width, long long height, long long max_iter, double x_min, double x_max, double y_min, double y_max)
{
    string pixels = py_bytearray();
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = height;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
    {
        double py = (y_min + ((y_max - y_min) * py_div(y, (height - 1))));
        auto __pytra_range_start_7 = 0;
        auto __pytra_range_stop_8 = width;
        auto __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
        {
            double px = (x_min + ((x_max - x_min) * py_div(x, (width - 1))));
            long long it = escape_count(px, py, max_iter);
            long long r;
            long long g;
            long long b;
            if ((it >= max_iter))
            {
                r = 0;
                g = 0;
                b = 0;
            }
            else
            {
                double t = py_div(it, max_iter);
                r = static_cast<long long>((255.0 * (t * t)));
                g = static_cast<long long>((255.0 * t));
                b = static_cast<long long>((255.0 * (1.0 - t)));
            }
            pixels.push_back(r);
            pixels.push_back(g);
            pixels.push_back(b);
        }
    }
    return pixels;
}

void run_mandelbrot()
{
    long long width = 800;
    long long height = 600;
    long long max_iter = 400;
    string out_path = "sample/out/mandelbrot_01.png";
    double start = perf_counter();
    string pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2);
    pycs::cpp_module::png::write_rgb_png(out_path, width, height, pixels);
    double elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_mandelbrot();
    return 0;
}
