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

vector<vector<int>> next_state(const vector<vector<int>>& grid, int w, int h)
{
    vector<vector<int>> nxt = {};
    auto y = 0;
    while ((y < h))
    {
        vector<int> row = {};
        auto x = 0;
        while ((x < w))
        {
            auto cnt = 0;
            auto dy = (-1);
            while ((dy <= 1))
            {
                auto dx = (-1);
                while ((dx <= 1))
                {
                    if (((dx != 0) || (dy != 0)))
                    {
                        auto nx = (((x + dx) + w) % w);
                        auto ny = (((y + dy) + h) % h);
                        cnt = (cnt + grid[ny][nx]);
                    }
                    dx = (dx + 1);
                }
                dy = (dy + 1);
            }
            auto alive = grid[y][x];
            if (((alive == 1) && ((cnt == 2) || (cnt == 3))))
            {
                row.push_back(1);
            }
            else
            {
                if (((alive == 0) && (cnt == 3)))
                {
                    row.push_back(1);
                }
                else
                {
                    row.push_back(0);
                }
            }
            x = (x + 1);
        }
        nxt.push_back(row);
        y = (y + 1);
    }
    return nxt;
}

string render(const vector<vector<int>>& grid, int w, int h, int cell)
{
    auto width = (w * cell);
    auto height = (h * cell);
    auto frame = string(static_cast<size_t>((width * height)), '\0');
    auto y = 0;
    while ((y < h))
    {
        auto x = 0;
        while ((x < w))
        {
            auto v = (grid[y][x] ? 255 : 0);
            auto yy = 0;
            while ((yy < cell))
            {
                auto base = ((((y * cell) + yy) * width) + (x * cell));
                auto xx = 0;
                while ((xx < cell))
                {
                    frame[(base + xx)] = v;
                    xx = (xx + 1);
                }
                yy = (yy + 1);
            }
            x = (x + 1);
        }
        y = (y + 1);
    }
    return frame;
}

void run_07_game_of_life_loop()
{
    auto w = 96;
    auto h = 72;
    auto cell = 3;
    auto steps = 70;
    auto out_path = "sample/out/07_game_of_life_loop.gif";
    auto start = perf_counter();
    vector<vector<int>> grid = {};
    auto y = 0;
    while ((y < h))
    {
        vector<int> row = {};
        auto x = 0;
        while ((x < w))
        {
            row.push_back(((((((x * 17) + (y * 31)) + 13) % 11) < 3) ? 1 : 0));
            x = (x + 1);
        }
        grid.push_back(row);
        y = (y + 1);
    }
    vector<string> frames = {};
    auto i = 0;
    while ((i < steps))
    {
        frames.push_back(render(grid, w, h, cell));
        grid = next_state(grid, w, h);
        i = (i + 1);
    }
    pycs::cpp_module::gif::save_gif(out_path, (w * cell), (h * cell), frames, pycs::cpp_module::gif::grayscale_palette(), 4, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", steps);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_07_game_of_life_loop();
    return 0;
}
