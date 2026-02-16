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

string fire_palette()
{
    auto p = string();
    auto i = 0;
    while ((i < 256))
    {
        auto r = 0;
        auto g = 0;
        auto b = 0;
        if ((i < 85))
        {
            r = (i * 3);
            g = 0;
            b = 0;
        }
        else
        {
            if ((i < 170))
            {
                r = 255;
                g = ((i - 85) * 3);
                b = 0;
            }
            else
            {
                r = 255;
                g = 255;
                b = ((i - 170) * 3);
            }
        }
        p.push_back(r);
        p.push_back(g);
        p.push_back(b);
        i = (i + 1);
    }
    return p;
}

void run_09_fire_simulation()
{
    auto w = 220;
    auto h = 140;
    auto steps = 110;
    auto out_path = "sample/out/09_fire_simulation.gif";
    auto start = perf_counter();
    vector<vector<int>> heat = {};
    auto gy = 0;
    while ((gy < h))
    {
        vector<int> row = {};
        auto gx = 0;
        while ((gx < w))
        {
            row.push_back(0);
            gx = (gx + 1);
        }
        heat.push_back(row);
        gy = (gy + 1);
    }
    vector<string> frames = {};
    auto t = 0;
    while ((t < steps))
    {
        auto x = 0;
        while ((x < w))
        {
            auto val = (170 + (((x * 13) + (t * 17)) % 86));
            // unsupported assignment
            x = (x + 1);
        }
        auto y = 1;
        while ((y < h))
        {
            x = 0;
            while ((x < w))
            {
                auto a = heat[y][x];
                auto b = heat[y][(((x - 1) + w) % w)];
                auto c = heat[y][((x + 1) % w)];
                auto d = heat[((y + 1) % h)][x];
                auto v = ((((a + b) + c) + d) / 4);
                auto cool = (1 + (((x + y) + t) % 3));
                auto nv = (v - cool);
                // unsupported assignment
                x = (x + 1);
            }
            y = (y + 1);
        }
        auto frame = string(static_cast<size_t>((w * h)), '\0');
        auto i = 0;
        auto yy = 0;
        while ((yy < h))
        {
            auto xx = 0;
            while ((xx < w))
            {
                // unsupported assignment
                i = (i + 1);
                xx = (xx + 1);
            }
            yy = (yy + 1);
        }
        frames.push_back(frame);
        t = (t + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, fire_palette(), 4, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_09_fire_simulation();
    return 0;
}
