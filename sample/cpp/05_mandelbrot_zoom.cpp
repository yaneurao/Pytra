#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/py_runtime_modules.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
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

string render_frame(int width, int height, double center_x, double center_y, double scale, int max_iter)
{
    auto frame = string(static_cast<size_t>((width * height)), '\0');
    auto y = 0;
    auto idx = 0;
    while ((y < height))
    {
        auto cy = (center_y + ((y - (height * 0.5)) * scale));
        auto x = 0;
        while ((x < width))
        {
            auto cx = (center_x + ((x - (width * 0.5)) * scale));
            auto zx = 0.0;
            auto zy = 0.0;
            auto i = 0;
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
            frame[idx] = int(((255.0 * i) / max_iter));
            idx = (idx + 1);
            x = (x + 1);
        }
        y = (y + 1);
    }
    return frame;
}

void run_05_mandelbrot_zoom()
{
    auto width = 320;
    auto height = 240;
    auto frame_count = 48;
    auto max_iter = 110;
    auto center_x = (-0.743643887037151);
    auto center_y = 0.13182590420533;
    auto base_scale = (3.2 / (width * 1.0));
    auto zoom_per_frame = 0.93;
    auto out_path = "sample/out/05_mandelbrot_zoom.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto i = 0;
    auto scale = base_scale;
    while ((i < frame_count))
    {
        frames.push_back(render_frame(width, height, center_x, center_y, scale, max_iter));
        scale = (scale * zoom_per_frame);
        i = (i + 1);
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
