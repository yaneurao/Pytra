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

vector<uint8_t> render_frame(long long width, long long height, double center_x, double center_y, double scale, long long max_iter)
{
    vector<uint8_t> frame = py_bytearray((width * height));
    long long idx = 0;
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = height;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
    {
        double cy = (center_y + ((y - (height * 0.5)) * scale));
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = width;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
        {
            double cx = (center_x + ((x - (width * 0.5)) * scale));
            double zx = 0.0;
            double zy = 0.0;
            long long i = 0;
            while ((i < max_iter))
            {
                auto zx2 = (zx * zx);
                auto zy2 = (zy * zy);
                if (((zx2 + zy2) > 4.0))
                {
                    break;
                }
                zy = (((2.0 * zx) * zy) + cy);
                zx = ((zx2 - zy2) + cx);
                i = (i + 1);
            }
            frame[idx] = static_cast<long long>(py_div((255.0 * i), max_iter));
            idx = (idx + 1);
        }
    }
    return py_bytes(frame);
}

void run_05_mandelbrot_zoom()
{
    long long width = 320;
    long long height = 240;
    long long frame_count = 48;
    long long max_iter = 110;
    double center_x = (-0.743643887037151);
    double center_y = 0.13182590420533;
    double base_scale = py_div(3.2, width);
    double zoom_per_frame = 0.93;
    string out_path = "sample/out/05_mandelbrot_zoom.gif";
    auto start = perf_counter();
    vector<vector<uint8_t>> frames = {};
    auto scale = base_scale;
    auto __pytra_range_start_7 = 0;
    auto __pytra_range_stop_8 = frame_count;
    auto __pytra_range_step_9 = 1;
    if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto _ = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (_ < __pytra_range_stop_8) : (_ > __pytra_range_stop_8); _ += __pytra_range_step_9)
    {
        frames.push_back(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale = (scale * zoom_per_frame);
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, pycs::cpp_module::gif::grayscale_palette(), 5, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frame_count);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_05_mandelbrot_zoom();
    return 0;
}
