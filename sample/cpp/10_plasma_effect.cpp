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

void run_10_plasma_effect()
{
    auto w = 320;
    auto h = 240;
    auto frames_n = 72;
    auto out_path = "sample/out/10_plasma_effect.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto t = 0;
    while ((t < frames_n))
    {
        auto frame = string(static_cast<size_t>((w * h)), '\0');
        auto i = 0;
        auto y = 0;
        while ((y < h))
        {
            auto x = 0;
            while ((x < w))
            {
                auto dx = (x - 160);
                auto dy = (y - 120);
                auto v = (((pycs::cpp_module::math::sin(((x + (t * 2.0)) * 0.045)) + pycs::cpp_module::math::sin(((y - (t * 1.2)) * 0.05))) + pycs::cpp_module::math::sin((((x + y) + (t * 1.7)) * 0.03))) + pycs::cpp_module::math::sin(((pycs::cpp_module::math::sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))));
                auto c = int(((v + 4.0) * (255.0 / 8.0)));
                if ((c < 0))
                {
                    c = 0;
                }
                if ((c > 255))
                {
                    c = 255;
                }
                frame[i] = c;
                i = (i + 1);
                x = (x + 1);
            }
            y = (y + 1);
        }
        frames.push_back(frame);
        t = (t + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_10_plasma_effect();
    return 0;
}
