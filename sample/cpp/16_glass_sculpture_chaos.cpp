#include "cpp_module/gc.h"
#include "cpp_module/gif.h"
#include "cpp_module/math.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
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

double dot(double ax, double ay, double az, double bx, double by, double bz)
{
    return (((ax * bx) + (ay * by)) + (az * bz));
}

double length(double x, double y, double z)
{
    return pycs::cpp_module::math::sqrt((((x * x) + (y * y)) + (z * z)));
}

tuple<double, double, double> normalize(double x, double y, double z)
{
    auto l = length(x, y, z);
    if ((l < 1e-09))
    {
        return std::make_tuple(0.0, 0.0, 0.0);
    }
    return std::make_tuple(py_div(x, l), py_div(y, l), py_div(z, l));
}

tuple<double, double, double> reflect(double ix, double iy, double iz, double nx, double ny, double nz)
{
    double d = (dot(ix, iy, iz, nx, ny, nz) * 2.0);
    return std::make_tuple((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)));
}

tuple<double, double, double> refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
{
    auto cosi = (-dot(ix, iy, iz, nx, ny, nz));
    auto sint2 = ((eta * eta) * (1.0 - (cosi * cosi)));
    if ((sint2 > 1.0))
    {
        return reflect(ix, iy, iz, nx, ny, nz);
    }
    auto cost = pycs::cpp_module::math::sqrt((1.0 - sint2));
    auto k = ((eta * cosi) - cost);
    return std::make_tuple(((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)));
}

double schlick(double cos_theta, double f0)
{
    double m = (1.0 - cos_theta);
    return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)));
}

tuple<double, double, double> sky_color(double dx, double dy, double dz, double tphase)
{
    double t = (0.5 * (dy + 1.0));
    double r = (0.06 + (0.2 * t));
    double g = (0.1 + (0.25 * t));
    double b = (0.16 + (0.45 * t));
    double band = (0.5 + (0.5 * pycs::cpp_module::math::sin((((8.0 * dx) + (6.0 * dz)) + tphase))));
    r = (r + (0.08 * band));
    g = (g + (0.05 * band));
    b = (b + (0.12 * band));
    return std::make_tuple(clamp01(r), clamp01(g), clamp01(b));
}

double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
{
    auto lx = (ox - cx);
    auto ly = (oy - cy);
    auto lz = (oz - cz);
    auto b = (((lx * dx) + (ly * dy)) + (lz * dz));
    auto c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius));
    auto h = ((b * b) - c);
    if ((h < 0.0))
    {
        return (-1.0);
    }
    auto s = pycs::cpp_module::math::sqrt(h);
    auto t0 = ((-b) - s);
    if ((t0 > 0.0001))
    {
        return t0;
    }
    auto t1 = ((-b) + s);
    if ((t1 > 0.0001))
    {
        return t1;
    }
    return (-1.0);
}

string palette_332()
{
    string p = py_bytearray((256 * 3));
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = 256;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        long long r = ((i >> 5) & 7);
        long long g = ((i >> 2) & 7);
        long long b = (i & 3);
        p[((i * 3) + 0)] = static_cast<long long>(py_div((255 * r), 7));
        p[((i * 3) + 1)] = static_cast<long long>(py_div((255 * g), 7));
        p[((i * 3) + 2)] = static_cast<long long>(py_div((255 * b), 3));
    }
    return py_bytes(p);
}

long long quantize_332(double r, double g, double b)
{
    long long rr = static_cast<long long>((clamp01(r) * 255.0));
    long long gg = static_cast<long long>((clamp01(g) * 255.0));
    long long bb = static_cast<long long>((clamp01(b) * 255.0));
    return ((((rr >> 5) << 5) + ((gg >> 5) << 2)) + (bb >> 6));
}

string render_frame(long long width, long long height, long long frame_id, long long frames_n)
{
    double t = py_div(frame_id, frames_n);
    double tphase = ((2.0 * pycs::cpp_module::math::pi) * t);
    double cam_r = 3.0;
    auto cam_x = (cam_r * pycs::cpp_module::math::cos((tphase * 0.9)));
    double cam_y = (1.1 + (0.25 * pycs::cpp_module::math::sin((tphase * 0.6))));
    auto cam_z = (cam_r * pycs::cpp_module::math::sin((tphase * 0.9)));
    double look_x = 0.0;
    double look_y = 0.35;
    double look_z = 0.0;
    auto __pytra_tuple_4 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z));
    auto fwd_x = std::get<0>(__pytra_tuple_4);
    auto fwd_y = std::get<1>(__pytra_tuple_4);
    auto fwd_z = std::get<2>(__pytra_tuple_4);
    auto __pytra_tuple_5 = normalize(fwd_z, 0.0, (-fwd_x));
    auto right_x = std::get<0>(__pytra_tuple_5);
    auto right_y = std::get<1>(__pytra_tuple_5);
    auto right_z = std::get<2>(__pytra_tuple_5);
    auto __pytra_tuple_6 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)));
    auto up_x = std::get<0>(__pytra_tuple_6);
    auto up_y = std::get<1>(__pytra_tuple_6);
    auto up_z = std::get<2>(__pytra_tuple_6);
    double s0x = (0.9 * pycs::cpp_module::math::cos((1.3 * tphase)));
    double s0y = (0.15 + (0.35 * pycs::cpp_module::math::sin((1.7 * tphase))));
    double s0z = (0.9 * pycs::cpp_module::math::sin((1.3 * tphase)));
    double s1x = (1.2 * pycs::cpp_module::math::cos(((1.3 * tphase) + 2.094)));
    double s1y = (0.1 + (0.4 * pycs::cpp_module::math::sin(((1.1 * tphase) + 0.8))));
    double s1z = (1.2 * pycs::cpp_module::math::sin(((1.3 * tphase) + 2.094)));
    double s2x = (1.0 * pycs::cpp_module::math::cos(((1.3 * tphase) + 4.188)));
    double s2y = (0.2 + (0.3 * pycs::cpp_module::math::sin(((1.5 * tphase) + 1.9))));
    double s2z = (1.0 * pycs::cpp_module::math::sin(((1.3 * tphase) + 4.188)));
    double lr = 0.35;
    double lx = (2.4 * pycs::cpp_module::math::cos((tphase * 1.8)));
    double ly = (1.8 + (0.8 * pycs::cpp_module::math::sin((tphase * 1.2))));
    double lz = (2.4 * pycs::cpp_module::math::sin((tphase * 1.8)));
    string frame = py_bytearray((width * height));
    double aspect = py_div(width, height);
    double fov = 1.25;
    long long i = 0;
    auto __pytra_range_start_7 = 0;
    auto __pytra_range_stop_8 = height;
    auto __pytra_range_step_9 = 1;
    if (__pytra_range_step_9 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto py = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (py < __pytra_range_stop_8) : (py > __pytra_range_stop_8); py += __pytra_range_step_9)
    {
        double sy = (1.0 - py_div((2.0 * (py + 0.5)), height));
        auto __pytra_range_start_10 = 0;
        auto __pytra_range_stop_11 = width;
        auto __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto px = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (px < __pytra_range_stop_11) : (px > __pytra_range_stop_11); px += __pytra_range_step_12)
        {
            double sx = ((py_div((2.0 * (px + 0.5)), width) - 1.0) * aspect);
            auto rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))));
            auto ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))));
            auto rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))));
            auto __pytra_tuple_13 = normalize(rx, ry, rz);
            auto dx = std::get<0>(__pytra_tuple_13);
            auto dy = std::get<1>(__pytra_tuple_13);
            auto dz = std::get<2>(__pytra_tuple_13);
            double best_t = 1000000000.0;
            long long hit_kind = 0;
            double r = 0.0;
            double g = 0.0;
            double b = 0.0;
            if ((dy < (-1e-06)))
            {
                double tf = py_div(((-1.2) - cam_y), dy);
                if (((tf > 0.0001) && (tf < best_t)))
                {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            auto t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (((t0 > 0.0) && (t0 < best_t)))
            {
                best_t = t0;
                hit_kind = 2;
            }
            auto t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (((t1 > 0.0) && (t1 < best_t)))
            {
                best_t = t1;
                hit_kind = 3;
            }
            auto t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (((t2 > 0.0) && (t2 < best_t)))
            {
                best_t = t2;
                hit_kind = 4;
            }
            if ((hit_kind == 0))
            {
                auto __pytra_tuple_14 = sky_color(dx, dy, dz, tphase);
                r = std::get<0>(__pytra_tuple_14);
                g = std::get<1>(__pytra_tuple_14);
                b = std::get<2>(__pytra_tuple_14);
            }
            else
            {
                if ((hit_kind == 1))
                {
                    auto hx = (cam_x + (best_t * dx));
                    auto hz = (cam_z + (best_t * dz));
                    long long cx = static_cast<long long>(pycs::cpp_module::math::floor((hx * 2.0)));
                    long long cz = static_cast<long long>(pycs::cpp_module::math::floor((hz * 2.0)));
                    auto checker = ((((cx + cz) % 2) == 0) ? 0 : 1);
                    auto base_r = ((checker == 0) ? 0.1 : 0.04);
                    auto base_g = ((checker == 0) ? 0.11 : 0.05);
                    auto base_b = ((checker == 0) ? 0.13 : 0.08);
                    auto lxv = (lx - hx);
                    double lyv = (ly - (-1.2));
                    auto lzv = (lz - hz);
                    auto __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                    auto ldx = std::get<0>(__pytra_tuple_15);
                    auto ldy = std::get<1>(__pytra_tuple_15);
                    auto ldz = std::get<2>(__pytra_tuple_15);
                    auto ndotl = max(ldy, 0.0);
                    auto ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv));
                    double glow = py_div(8.0, (1.0 + ldist2));
                    r = ((base_r + (0.8 * glow)) + (0.2 * ndotl));
                    g = ((base_g + (0.5 * glow)) + (0.18 * ndotl));
                    b = ((base_b + (1.0 * glow)) + (0.24 * ndotl));
                }
                else
                {
                    double cx = 0.0;
                    double cy = 0.0;
                    double cz = 0.0;
                    double rad = 1.0;
                    if ((hit_kind == 2))
                    {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    }
                    else
                    {
                        if ((hit_kind == 3))
                        {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        }
                        else
                        {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    auto hx = (cam_x + (best_t * dx));
                    auto hy = (cam_y + (best_t * dy));
                    auto hz = (cam_z + (best_t * dz));
                    auto __pytra_tuple_16 = normalize(py_div((hx - cx), rad), py_div((hy - cy), rad), py_div((hz - cz), rad));
                    auto nx = std::get<0>(__pytra_tuple_16);
                    auto ny = std::get<1>(__pytra_tuple_16);
                    auto nz = std::get<2>(__pytra_tuple_16);
                    auto __pytra_tuple_17 = reflect(dx, dy, dz, nx, ny, nz);
                    auto rdx = std::get<0>(__pytra_tuple_17);
                    auto rdy = std::get<1>(__pytra_tuple_17);
                    auto rdz = std::get<2>(__pytra_tuple_17);
                    auto __pytra_tuple_18 = refract(dx, dy, dz, nx, ny, nz, py_div(1.0, 1.45));
                    auto tdx = std::get<0>(__pytra_tuple_18);
                    auto tdy = std::get<1>(__pytra_tuple_18);
                    auto tdz = std::get<2>(__pytra_tuple_18);
                    auto __pytra_tuple_19 = sky_color(rdx, rdy, rdz, tphase);
                    auto sr = std::get<0>(__pytra_tuple_19);
                    auto sg = std::get<1>(__pytra_tuple_19);
                    auto sb = std::get<2>(__pytra_tuple_19);
                    auto __pytra_tuple_20 = sky_color(tdx, tdy, tdz, (tphase + 0.8));
                    auto tr = std::get<0>(__pytra_tuple_20);
                    auto tg = std::get<1>(__pytra_tuple_20);
                    auto tb = std::get<2>(__pytra_tuple_20);
                    auto cosi = max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0);
                    auto fr = schlick(cosi, 0.04);
                    r = ((tr * (1.0 - fr)) + (sr * fr));
                    g = ((tg * (1.0 - fr)) + (sg * fr));
                    b = ((tb * (1.0 - fr)) + (sb * fr));
                    auto lxv = (lx - hx);
                    auto lyv = (ly - hy);
                    auto lzv = (lz - hz);
                    auto __pytra_tuple_21 = normalize(lxv, lyv, lzv);
                    auto ldx = std::get<0>(__pytra_tuple_21);
                    auto ldy = std::get<1>(__pytra_tuple_21);
                    auto ldz = std::get<2>(__pytra_tuple_21);
                    auto ndotl = max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0);
                    auto __pytra_tuple_22 = normalize((ldx - dx), (ldy - dy), (ldz - dz));
                    auto hvx = std::get<0>(__pytra_tuple_22);
                    auto hvy = std::get<1>(__pytra_tuple_22);
                    auto hvz = std::get<2>(__pytra_tuple_22);
                    auto ndoth = max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0);
                    auto spec = (ndoth * ndoth);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    spec = (spec * spec);
                    double glow = py_div(10.0, (((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)));
                    r = (r + (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow)));
                    g = (g + (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow)));
                    b = (b + (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow)));
                    if ((hit_kind == 2))
                    {
                        r = (r * 0.95);
                        g = (g * 1.05);
                        b = (b * 1.1);
                    }
                    else
                    {
                        if ((hit_kind == 3))
                        {
                            r = (r * 1.08);
                            g = (g * 0.98);
                            b = (b * 1.04);
                        }
                        else
                        {
                            r = (r * 1.02);
                            g = (g * 1.1);
                            b = (b * 0.95);
                        }
                    }
                }
            }
            r = pycs::cpp_module::math::sqrt(clamp01(r));
            g = pycs::cpp_module::math::sqrt(clamp01(g));
            b = pycs::cpp_module::math::sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i = (i + 1);
        }
    }
    return py_bytes(frame);
}

void run_16_glass_sculpture_chaos()
{
    long long width = 320;
    long long height = 240;
    long long frames_n = 72;
    string out_path = "sample/out/16_glass_sculpture_chaos.gif";
    auto start = perf_counter();
    vector<string> frames = {};
    auto __pytra_range_start_23 = 0;
    auto __pytra_range_stop_24 = frames_n;
    auto __pytra_range_step_25 = 1;
    if (__pytra_range_step_25 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_23; (__pytra_range_step_25 > 0) ? (i < __pytra_range_stop_24) : (i > __pytra_range_stop_24); i += __pytra_range_step_25)
    {
        frames.push_back(render_frame(width, height, i, frames_n));
    }
    pycs::cpp_module::gif::save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    auto elapsed = (perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_16_glass_sculpture_chaos();
    return 0;
}
