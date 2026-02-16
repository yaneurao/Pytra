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

string render(const vector<int>& values, int w, int h)
{
    auto frame = string(static_cast<size_t>((w * h)), '\0');
    auto n = py_len(values);
    auto bar_w = ((w * 1.0) / n);
    auto i = 0;
    while ((i < n))
    {
        auto x0 = int((i * bar_w));
        auto x1 = int(((i + 1) * bar_w));
        if ((x1 <= x0))
        {
            x1 = (x0 + 1);
        }
        auto bh = int((((values[i] * 1.0) / n) * h));
        auto y = (h - bh);
        while ((y < h))
        {
            auto x = x0;
            while ((x < x1))
            {
                frame[((y * w) + x)] = 255;
                x = (x + 1);
            }
            y = (y + 1);
        }
        i = (i + 1);
    }
    return frame;
}

void run_12_sort_visualizer()
{
    auto w = 320;
    auto h = 180;
    auto n = 72;
    auto out_path = "sample/out/12_sort_visualizer.gif";
    auto start = perf_counter();
    vector<int> values = {};
    auto i = 0;
    while ((i < n))
    {
        values.push_back((((i * 37) + 19) % n));
        i = (i + 1);
    }
    vector<string> frames = {render(values, w, h)};
    i = 0;
    auto op = 0;
    while ((i < n))
    {
        auto j = 0;
        auto swapped = false;
        while ((j < ((n - i) - 1)))
        {
            if ((values[j] > values[(j + 1)]))
            {
                auto tmp = values[j];
                values[j] = values[(j + 1)];
                values[(j + 1)] = tmp;
                swapped = true;
            }
            if (((op % 8) == 0))
            {
                frames.push_back(render(values, w, h));
            }
            op = (op + 1);
            j = (j + 1);
        }
        if ((!swapped))
        {
            break;
        }
        i = (i + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, w, h, frames, pycs::cpp_module::gif::grayscale_palette(), 3, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", py_len(frames));
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_12_sort_visualizer();
    return 0;
}
