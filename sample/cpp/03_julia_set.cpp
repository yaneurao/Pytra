#include "cpp_module/gc.h"
#include "cpp_module/png.h"
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

string render_julia(int width, int height, int max_iter, double cx, double cy)
{
    string pixels = string();
    int y = 0;
    while ((y < height))
    {
        double zy0 = ((-1.2) + (2.4 * ((y * 1.0) / ((height - 1) * 1.0))));
        int x = 0;
        while ((x < width))
        {
            double zx = ((-1.8) + (3.6 * ((x * 1.0) / ((width - 1) * 1.0))));
            double zy = zy0;
            int i = 0;
            while ((i < max_iter))
            {
                double zx2 = (zx * zx);
                double zy2 = (zy * zy);
                if (((zx2 + zy2) > 4.0))
                {
                    break;
                }
                zy = (((2.0 * zx) * zy) + cy);
                zx = ((zx2 - zy2) + cx);
                i = (i + 1);
            }
            int r = 0;
            int g = 0;
            int b = 0;
            if ((i >= max_iter))
            {
                r = 0;
                g = 0;
                b = 0;
            }
            else
            {
                double t = ((i * 1.0) / (max_iter * 1.0));
                r = int((255.0 * (0.2 + (0.8 * t))));
                g = int((255.0 * (0.1 + (0.9 * (t * t)))));
                b = int((255.0 * (1.0 - t)));
            }
            pixels.push_back(r);
            pixels.push_back(g);
            pixels.push_back(b);
            x = (x + 1);
        }
        y = (y + 1);
    }
    return pixels;
}

void run_julia()
{
    int width = 1280;
    int height = 720;
    int max_iter = 520;
    string out_path = "sample/out/julia_03.png";
    double start = perf_counter();
    string pixels = render_julia(width, height, max_iter, (-0.8), 0.156);
    pycs::cpp_module::png::write_rgb_png(out_path, width, height, pixels);
    double elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_julia();
    return 0;
}
