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

string render_frame(int width, int height, double cr, double ci, int max_iter)
{
    auto frame = string(static_cast<size_t>((width * height)), '\0');
    auto y = 0;
    auto idx = 0;
    while ((y < height))
    {
        auto zy0 = ((-1.2) + (2.4 * ((y * 1.0) / (height - 1))));
        auto x = 0;
        while ((x < width))
        {
            auto zx = ((-1.8) + (3.6 * ((x * 1.0) / (width - 1))));
            auto zy = zy0;
            auto i = 0;
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
            frame[idx] = int(((255.0 * i) / max_iter));
            idx = (idx + 1);
            x = (x + 1);
        }
        y = (y + 1);
    }
    return frame;
}

void run_06_julia_parameter_sweep()
{
    auto width = 320;
    auto height = 240;
    auto frames_n = 50;
    auto max_iter = 120;
    auto out_path = "sample/out/06_julia_parameter_sweep.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto i = 0;
    while ((i < frames_n))
    {
        auto t = ((i * 1.0) / frames_n);
        auto cr = ((-0.8) + (0.32 * t));
        auto ci = (0.156 + (0.22 * (0.5 - t)));
        frames.push_back(render_frame(width, height, cr, ci, max_iter));
        i = (i + 1);
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
