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

string capture(const vector<vector<int>>& grid, int w, int h)
{
    auto frame = string(static_cast<size_t>((w * h)), '\0');
    auto i = 0;
    auto y = 0;
    while ((y < h))
    {
        auto x = 0;
        while ((x < w))
        {
            // unsupported assignment
            i = (i + 1);
            x = (x + 1);
        }
        y = (y + 1);
    }
    return frame;
}

void run_08_langtons_ant()
{
    auto w = 240;
    auto h = 240;
    auto out_path = "sample/out/08_langtons_ant.gif";
    auto start = perf_counter();
    vector<vector<int>> grid = {};
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
        grid.push_back(row);
        gy = (gy + 1);
    }
    auto x = (w / 2);
    auto y = (h / 2);
    auto d = 0;
    auto steps_total = 180000;
    auto capture_every = 3000;
    vector<string> frames = {};
    auto i = 0;
    while ((i < steps_total))
    {
        if ((grid[y][x] == 0))
        {
            d = ((d + 1) % 4);
            // unsupported assignment
        }
        else
        {
            d = ((d + 3) % 4);
            // unsupported assignment
        }
        if ((d == 0))
        {
            y = (((y - 1) + h) % h);
        }
        else
        {
            if ((d == 1))
            {
                x = ((x + 1) % w);
            }
            else
            {
                if ((d == 2))
                {
                    y = ((y + 1) % h);
                }
                else
                {
                    x = (((x - 1) + w) % w);
                }
            }
        }
        if (((i % capture_every) == 0))
        {
            frames.push_back(capture(grid, w, h));
        }
        i = (i + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 5, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_08_langtons_ant();
    return 0;
}
