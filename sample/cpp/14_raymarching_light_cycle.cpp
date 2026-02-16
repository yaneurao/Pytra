#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
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

string palette()
{
    auto p = string();
    auto i = 0;
    while ((i < 256))
    {
        auto r = int((20 + (i * 0.9)));
        if ((r > 255))
        {
            r = 255;
        }
        auto g = int((10 + (i * 0.7)));
        if ((g > 255))
        {
            g = 255;
        }
        auto b = int((30 + (i * 1.0)));
        if ((b > 255))
        {
            b = 255;
        }
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
        i = (i + 1);
    }
    return p;
}

int scene(double x, double y, double light_x, double light_y)
{
    auto x1 = (x + 0.45);
    auto y1 = (y + 0.2);
    auto x2 = (x - 0.35);
    auto y2 = (y - 0.15);
    auto r1 = pycs::cpp_module::math::sqrt(((x1 * x1) + (y1 * y1)));
    auto r2 = pycs::cpp_module::math::sqrt(((x2 * x2) + (y2 * y2)));
    auto blob = (pycs::cpp_module::math::exp((((-7.0) * r1) * r1)) + pycs::cpp_module::math::exp((((-8.0) * r2) * r2)));
    auto lx = (x - light_x);
    auto ly = (y - light_y);
    auto l = pycs::cpp_module::math::sqrt(((lx * lx) + (ly * ly)));
    auto lit = (1.0 / (1.0 + ((3.5 * l) * l)));
    auto v = int((((255.0 * blob) * lit) * 5.0));
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
    auto w = 320;
    auto h = 240;
    auto frames_n = 84;
    auto out_path = "sample/out/14_raymarching_light_cycle.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto t = 0;
    while ((t < frames_n))
    {
        auto frame = string(static_cast<size_t>((w * h)), '\0');
        auto a = (((t / frames_n) * pycs::cpp_module::math::pi) * 2.0);
        auto light_x = (0.75 * pycs::cpp_module::math::cos(a));
        auto light_y = (0.55 * pycs::cpp_module::math::sin((a * 1.2)));
        auto i = 0;
        auto y = 0;
        while ((y < h))
        {
            auto py = (((y / (h - 1)) * 2.0) - 1.0);
            auto x = 0;
            while ((x < w))
            {
                auto px = (((x / (w - 1)) * 2.0) - 1.0);
                // unsupported assignment
                i = (i + 1);
                x = (x + 1);
            }
            y = (y + 1);
        }
        frames.push_back(frame);
        t = (t + 1);
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
