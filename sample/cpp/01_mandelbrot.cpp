#include "cpp_module/gc.h"
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

int escape_count(double cx, double cy, int max_iter)
{
    double x = 0.0;
    double y = 0.0;
    int i = 0;
    while ((i < max_iter))
    {
        double x2 = (x * x);
        double y2 = (y * y);
        if (((x2 + y2) > 4.0))
        {
            return i;
        }
        y = (((2.0 * x) * y) + cy);
        x = ((x2 - y2) + cx);
        i = (i + 1);
    }
    return max_iter;
}

tuple<int, int, int> color_map(int iter_count, int max_iter)
{
    if ((iter_count >= max_iter))
    {
        return std::make_tuple(0, 0, 0);
    }
    double t = ((iter_count * 1.0) / (max_iter * 1.0));
    int r = int((255.0 * (t * t)));
    int g = int((255.0 * t));
    int b = int((255.0 * (1.0 - t)));
    return std::make_tuple(r, g, b);
}

string render_mandelbrot(int width, int height, int max_iter, double x_min, double x_max, double y_min, double y_max)
{
    string pixels = string();
    int y = 0;
    while ((y < height))
    {
        double py = (y_min + ((y_max - y_min) * ((y * 1.0) / ((height - 1) * 1.0))));
        int x = 0;
        while ((x < width))
        {
            double px = (x_min + ((x_max - x_min) * ((x * 1.0) / ((width - 1) * 1.0))));
            int it = escape_count(px, py, max_iter);
            int r;
            int g;
            int b;
            if ((it >= max_iter))
            {
                r = 0;
                g = 0;
                b = 0;
            }
            else
            {
                double t = ((it * 1.0) / (max_iter * 1.0));
                r = int((255.0 * (t * t)));
                g = int((255.0 * t));
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

void write_ppm(const string& path, int width, int height, const string& pixels)
{
    string header = (((("P6\n" + py_to_string(width)) + " ") + py_to_string(height)) + "\n255\n");
    auto f = std::make_shared<std::ofstream>(path, std::ios::binary);
    py_write(*f, header);
    py_write(*f, pixels);
    f->close();
}

void run_mandelbrot()
{
    int width = 800;
    int height = 600;
    int max_iter = 400;
    string out_path = "sample/out/mandelbrot_01.ppm";
    double start = perf_counter();
    string pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2);
    write_ppm(out_path, width, height, pixels);
    double elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("max_iter:", max_iter);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_mandelbrot();
    return 0;
}
