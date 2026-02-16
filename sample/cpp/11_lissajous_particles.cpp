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

string color_palette()
{
    auto p = string();
    auto i = 0;
    while ((i < 256))
    {
        auto r = i;
        auto g = ((i * 3) % 256);
        auto b = (255 - i);
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
        i = (i + 1);
    }
    return p;
}

void run_11_lissajous_particles()
{
    auto w = 320;
    auto h = 240;
    auto frames_n = 80;
    auto particles = 24;
    auto out_path = "sample/out/11_lissajous_particles.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto t = 0;
    while ((t < frames_n))
    {
        auto frame = string(static_cast<size_t>((w * h)), '\0');
        auto p = 0;
        while ((p < particles))
        {
            auto phase = (p * 0.261799);
            auto x = int(((w * 0.5) + ((w * 0.38) * pycs::cpp_module::math::sin(((0.11 * t) + (phase * 2.0))))));
            auto y = int(((h * 0.5) + ((h * 0.38) * pycs::cpp_module::math::sin(((0.17 * t) + (phase * 3.0))))));
            auto color = (30 + ((p * 9) % 220));
            auto dy = (-2);
            while ((dy <= 2))
            {
                auto dx = (-2);
                while ((dx <= 2))
                {
                    auto xx = (x + dx);
                    auto yy = (y + dy);
                    if (((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)))
                    {
                        auto d2 = ((dx * dx) + (dy * dy));
                        if ((d2 <= 4))
                        {
                            auto idx = ((yy * w) + xx);
                            auto v = (color - (d2 * 20));
                            if ((v < 0))
                            {
                                v = 0;
                            }
                            if ((v > frame[idx]))
                            {
                                frame[idx] = v;
                            }
                        }
                    }
                    dx = (dx + 1);
                }
                dy = (dy + 1);
            }
            p = (p + 1);
        }
        frames.push_back(frame);
        t = (t + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, color_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_11_lissajous_particles();
    return 0;
}
