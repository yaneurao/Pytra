#include "cpp_module/gc.h"
#include "cpp_module/math.h"
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

double clamp01(double v)
{
    if ((v < 0.0))
    {
        return 0.0;
    }
    if ((v > 1.0))
    {
        return 1.0;
    }
    return v;
}

double hit_sphere(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double r)
{
    double lx = (ox - cx);
    double ly = (oy - cy);
    double lz = (oz - cz);
    double a = (((dx * dx) + (dy * dy)) + (dz * dz));
    double b = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)));
    double c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r));
    double d = ((b * b) - ((4.0 * a) * c));
    if ((d < 0.0))
    {
        return (-1.0);
    }
    double sd = pycs::cpp_module::math::sqrt(d);
    double t0 = (((-b) - sd) / (2.0 * a));
    double t1 = (((-b) + sd) / (2.0 * a));
    if ((t0 > 0.001))
    {
        return t0;
    }
    if ((t1 > 0.001))
    {
        return t1;
    }
    return (-1.0);
}

string render(int width, int height)
{
    string pixels = string();
    double ox = 0.0;
    double oy = 0.0;
    double oz = (-3.0);
    double lx = (-0.4);
    double ly = 0.8;
    double lz = (-0.45);
    int y = 0;
    while ((y < height))
    {
        double sy = (1.0 - (2.0 * ((y * 1.0) / ((height - 1) * 1.0))));
        int x = 0;
        while ((x < width))
        {
            double sx = ((2.0 * ((x * 1.0) / ((width - 1) * 1.0))) - 1.0);
            sx = (sx * ((width * 1.0) / (height * 1.0)));
            double dx = sx;
            double dy = sy;
            double dz = 1.0;
            double inv_len = (1.0 / pycs::cpp_module::math::sqrt((((dx * dx) + (dy * dy)) + (dz * dz))));
            dx = (dx * inv_len);
            dy = (dy * inv_len);
            dz = (dz * inv_len);
            double t_min = 1e+30;
            int hit_id = (-1);
            double t = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8);
            if (((t > 0.0) && (t < t_min)))
            {
                t_min = t;
                hit_id = 0;
            }
            t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
            if (((t > 0.0) && (t < t_min)))
            {
                t_min = t;
                hit_id = 1;
            }
            t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0);
            if (((t > 0.0) && (t < t_min)))
            {
                t_min = t;
                hit_id = 2;
            }
            int r = 0;
            int g = 0;
            int b = 0;
            if ((hit_id >= 0))
            {
                double px = (ox + (dx * t_min));
                double py = (oy + (dy * t_min));
                double pz = (oz + (dz * t_min));
                double nx = 0.0;
                double ny = 0.0;
                double nz = 0.0;
                if ((hit_id == 0))
                {
                    nx = ((px + 0.8) / 0.8);
                    ny = ((py + 0.2) / 0.8);
                    nz = ((pz - 2.2) / 0.8);
                }
                else
                {
                    if ((hit_id == 1))
                    {
                        nx = ((px - 0.9) / 0.95);
                        ny = ((py - 0.1) / 0.95);
                        nz = ((pz - 2.9) / 0.95);
                    }
                    else
                    {
                        nx = 0.0;
                        ny = 1.0;
                        nz = 0.0;
                    }
                }
                double diff = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)));
                diff = clamp01(diff);
                double base_r = 0.0;
                double base_g = 0.0;
                double base_b = 0.0;
                if ((hit_id == 0))
                {
                    base_r = 0.95;
                    base_g = 0.35;
                    base_b = 0.25;
                }
                else
                {
                    if ((hit_id == 1))
                    {
                        base_r = 0.25;
                        base_g = 0.55;
                        base_b = 0.95;
                    }
                    else
                    {
                        int checker = (int(((px + 50.0) * 0.8)) + int(((pz + 50.0) * 0.8)));
                        if (((checker % 2) == 0))
                        {
                            base_r = 0.85;
                            base_g = 0.85;
                            base_b = 0.85;
                        }
                        else
                        {
                            base_r = 0.2;
                            base_g = 0.2;
                            base_b = 0.2;
                        }
                    }
                }
                double shade = (0.12 + (0.88 * diff));
                r = int((255.0 * clamp01((base_r * shade))));
                g = int((255.0 * clamp01((base_g * shade))));
                b = int((255.0 * clamp01((base_b * shade))));
            }
            else
            {
                double tsky = (0.5 * (dy + 1.0));
                r = int((255.0 * (0.65 + (0.2 * tsky))));
                g = int((255.0 * (0.75 + (0.18 * tsky))));
                b = int((255.0 * (0.9 + (0.08 * tsky))));
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

void run_raytrace()
{
    int width = 960;
    int height = 540;
    string out_path = "sample/out/raytrace_02.png";
    double start = perf_counter();
    string pixels = render(width, height);
    pycs::cpp_module::png::write_rgb_png(out_path, width, height, pixels);
    double elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_raytrace();
    return 0;
}
