#include "cpp_module/py_runtime.h"





float64 clamp01(float64 v) {
    if (v < 0.0)
        return 0.0;
    if (v > 1.0)
        return 1.0;
    return v;
}

float64 dot(float64 ax, float64 ay, float64 az, float64 bx, float64 by, float64 bz) {
    return ax * bx + ay * by + az * bz;
}

float64 length(float64 x, float64 y, float64 z) {
    return py_math::sqrt(x * x + y * y + z * z);
}

std::tuple<float64, float64, float64> normalize(float64 x, float64 y, float64 z) {
    float64 l = length(x, y, z);
    if (l < 1e-09)
        return std::make_tuple(0.0, 0.0, 0.0);
    return std::make_tuple(x / l, y / l, z / l);
}

std::tuple<float64, float64, float64> reflect(float64 ix, float64 iy, float64 iz, float64 nx, float64 ny, float64 nz) {
    float64 d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
    return std::make_tuple(ix - d * nx, iy - d * ny, iz - d * nz);
}

std::tuple<float64, float64, float64> refract(float64 ix, float64 iy, float64 iz, float64 nx, float64 ny, float64 nz, float64 eta) {
    float64 cosi = -dot(ix, iy, iz, nx, ny, nz);
    float64 sint2 = eta * eta * (1.0 - cosi * cosi);
    if (sint2 > 1.0)
        return reflect(ix, iy, iz, nx, ny, nz);
    float64 cost = py_math::sqrt(1.0 - sint2);
    float64 k = eta * cosi - cost;
    return std::make_tuple(eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
}

float64 schlick(float64 cos_theta, float64 f0) {
    float64 m = 1.0 - cos_theta;
    return f0 + (1.0 - f0) * m * m * m * m * m;
}

std::tuple<float64, float64, float64> sky_color(float64 dx, float64 dy, float64 dz, float64 tphase) {
    float64 t = 0.5 * (dy + 1.0);
    float64 r = 0.06 + 0.2 * t;
    float64 g = 0.1 + 0.25 * t;
    float64 b = 0.16 + 0.45 * t;
    float64 band = 0.5 + 0.5 * py_math::sin(8.0 * dx + 6.0 * dz + tphase);
    r += 0.08 * band;
    g += 0.05 * band;
    b += 0.12 * band;
    return std::make_tuple(clamp01(r), clamp01(g), clamp01(b));
}

float64 sphere_intersect(float64 ox, float64 oy, float64 oz, float64 dx, float64 dy, float64 dz, float64 cx, float64 cy, float64 cz, float64 radius) {
    float64 lx = ox - cx;
    float64 ly = oy - cy;
    float64 lz = oz - cz;
    float64 b = lx * dx + ly * dy + lz * dz;
    float64 c = lx * lx + ly * ly + lz * lz - radius * radius;
    float64 h = b * b - c;
    if (h < 0.0)
        return -1.0;
    float64 s = py_math::sqrt(h);
    float64 t0 = -b - s;
    if (t0 > 0.0001)
        return t0;
    float64 t1 = -b + s;
    if (t1 > 0.0001)
        return t1;
    return -1.0;
}

list<uint8> palette_332() {
    int64 r;
    int64 g;
    int64 b;
    
    list<uint8> p = list<uint8>(256 * 3);
    for (int64 i = 0; i < 256; ++i) {
        r = i >> 5 & 7;
        g = i >> 2 & 7;
        b = i & 3;
        p[i * 3 + 0] = int64(static_cast<float64>(255 * r) / static_cast<float64>(7));
        p[i * 3 + 1] = int64(static_cast<float64>(255 * g) / static_cast<float64>(7));
        p[i * 3 + 2] = int64(static_cast<float64>(255 * b) / static_cast<float64>(3));
    }
    return list<uint8>(p);
}

int64 quantize_332(float64 r, float64 g, float64 b) {
    int64 rr = int64(clamp01(r) * 255.0);
    int64 gg = int64(clamp01(g) * 255.0);
    int64 bb = int64(clamp01(b) * 255.0);
    return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
}

list<uint8> render_frame(int64 width, int64 height, int64 frame_id, int64 frames_n) {
    float64 fwd_x;
    float64 fwd_y;
    float64 fwd_z;
    float64 right_x;
    float64 right_y;
    float64 right_z;
    float64 up_x;
    float64 up_y;
    float64 up_z;
    float64 sy;
    float64 sx;
    float64 rx;
    float64 ry;
    float64 rz;
    float64 dx;
    float64 dy;
    float64 dz;
    float64 best_t;
    int64 hit_kind;
    float64 r;
    float64 g;
    float64 b;
    float64 tf;
    float64 t0;
    float64 t1;
    float64 t2;
    float64 hx;
    float64 hz;
    int64 cx;
    int64 cz;
    int64 checker;
    float64 base_r;
    float64 base_g;
    float64 base_b;
    float64 lxv;
    float64 lyv;
    float64 lzv;
    float64 ldx;
    float64 ldy;
    float64 ldz;
    float64 ndotl;
    float64 ldist2;
    float64 glow;
    float64 cy;
    float64 rad;
    float64 hy;
    float64 nx;
    float64 ny;
    float64 nz;
    float64 rdx;
    float64 rdy;
    float64 rdz;
    float64 tdx;
    float64 tdy;
    float64 tdz;
    float64 sr;
    float64 sg;
    float64 sb;
    float64 tr;
    float64 tg;
    float64 tb;
    float64 cosi;
    float64 fr;
    float64 hvx;
    float64 hvy;
    float64 hvz;
    float64 ndoth;
    float64 spec;
    
    float64 t = static_cast<float64>(frame_id) / static_cast<float64>(frames_n);
    float64 tphase = 2.0 * py_math::pi * t;
    
    
    float64 cam_r = 3.0;
    float64 cam_x = cam_r * py_math::cos(tphase * 0.9);
    float64 cam_y = 1.1 + 0.25 * py_math::sin(tphase * 0.6);
    float64 cam_z = cam_r * py_math::sin(tphase * 0.9);
    float64 look_x = 0.0;
    float64 look_y = 0.35;
    float64 look_z = 0.0;
    
    auto __tuple_1 = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
    fwd_x = std::get<0>(__tuple_1);
    fwd_y = std::get<1>(__tuple_1);
    fwd_z = std::get<2>(__tuple_1);
    auto __tuple_2 = normalize(fwd_z, 0.0, -fwd_x);
    right_x = std::get<0>(__tuple_2);
    right_y = std::get<1>(__tuple_2);
    right_z = std::get<2>(__tuple_2);
    auto __tuple_3 = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
    up_x = std::get<0>(__tuple_3);
    up_y = std::get<1>(__tuple_3);
    up_z = std::get<2>(__tuple_3);
    
    
    float64 s0x = 0.9 * py_math::cos(1.3 * tphase);
    float64 s0y = 0.15 + 0.35 * py_math::sin(1.7 * tphase);
    float64 s0z = 0.9 * py_math::sin(1.3 * tphase);
    float64 s1x = 1.2 * py_math::cos(1.3 * tphase + 2.094);
    float64 s1y = 0.1 + 0.4 * py_math::sin(1.1 * tphase + 0.8);
    float64 s1z = 1.2 * py_math::sin(1.3 * tphase + 2.094);
    float64 s2x = 1.0 * py_math::cos(1.3 * tphase + 4.188);
    float64 s2y = 0.2 + 0.3 * py_math::sin(1.5 * tphase + 1.9);
    float64 s2z = 1.0 * py_math::sin(1.3 * tphase + 4.188);
    float64 lr = 0.35;
    float64 lx = 2.4 * py_math::cos(tphase * 1.8);
    float64 ly = 1.8 + 0.8 * py_math::sin(tphase * 1.2);
    float64 lz = 2.4 * py_math::sin(tphase * 1.8);
    
    list<uint8> frame = list<uint8>(width * height);
    float64 aspect = static_cast<float64>(width) / static_cast<float64>(height);
    float64 fov = 1.25;
    
    int64 i = 0;
    for (int64 py = 0; py < height; ++py) {
        sy = 1.0 - 2.0 * (static_cast<float64>(py) + 0.5) / static_cast<float64>(height);
        for (int64 px = 0; px < width; ++px) {
            sx = (2.0 * (static_cast<float64>(px) + 0.5) / static_cast<float64>(width) - 1.0) * aspect;
            rx = fwd_x + fov * (sx * right_x + sy * up_x);
            ry = fwd_y + fov * (sx * right_y + sy * up_y);
            rz = fwd_z + fov * (sx * right_z + sy * up_z);
            auto __tuple_4 = normalize(rx, ry, rz);
            dx = std::get<0>(__tuple_4);
            dy = std::get<1>(__tuple_4);
            dz = std::get<2>(__tuple_4);
            
            
            best_t = 1000000000.0;
            hit_kind = 0;
            r = 0.0;
            g = 0.0;
            b = 0.0;
            
            
            if (dy < -1e-06) {
                tf = (-1.2 - cam_y) / dy;
                if (tf > 0.0001 && tf < best_t) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            
            t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
            if (t0 > 0.0 && t0 < best_t) {
                best_t = t0;
                hit_kind = 2;
            }
            t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
            if (t1 > 0.0 && t1 < best_t) {
                best_t = t1;
                hit_kind = 3;
            }
            t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
            if (t2 > 0.0 && t2 < best_t) {
                best_t = t2;
                hit_kind = 4;
            }
            
            if (hit_kind == 0) {
                auto __tuple_5 = sky_color(dx, dy, dz, tphase);
                r = std::get<0>(__tuple_5);
                g = std::get<1>(__tuple_5);
                b = std::get<2>(__tuple_5);
            } else {
                if (hit_kind == 1) {
                    hx = cam_x + best_t * dx;
                    hz = cam_z + best_t * dz;
                    cx = int64(py_math::floor(hx * 2.0));
                    cz = int64(py_math::floor(hz * 2.0));
                    checker = ((cx + cz) % 2 == 0 ? 0 : 1);
                    base_r = (checker == 0 ? 0.1 : 0.04);
                    base_g = (checker == 0 ? 0.11 : 0.05);
                    base_b = (checker == 0 ? 0.13 : 0.08);
                    
                    lxv = lx - hx;
                    lyv = ly - -1.2;
                    lzv = lz - hz;
                    auto __tuple_6 = normalize(lxv, lyv, lzv);
                    ldx = std::get<0>(__tuple_6);
                    ldy = std::get<1>(__tuple_6);
                    ldz = std::get<2>(__tuple_6);
                    ndotl = std::max<float64>(static_cast<float64>(ldy), static_cast<float64>(0.0));
                    ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                    glow = 8.0 / (1.0 + ldist2);
                    r = base_r + 0.8 * glow + 0.2 * ndotl;
                    g = base_g + 0.5 * glow + 0.18 * ndotl;
                    b = base_b + 1.0 * glow + 0.24 * ndotl;
                } else {
                    cx = 0.0;
                    cy = 0.0;
                    cz = 0.0;
                    rad = 1.0;
                    if (hit_kind == 2) {
                        cx = s0x;
                        cy = s0y;
                        cz = s0z;
                        rad = 0.65;
                    } else {
                        if (hit_kind == 3) {
                            cx = s1x;
                            cy = s1y;
                            cz = s1z;
                            rad = 0.72;
                        } else {
                            cx = s2x;
                            cy = s2y;
                            cz = s2z;
                            rad = 0.58;
                        }
                    }
                    hx = cam_x + best_t * dx;
                    hy = cam_y + best_t * dy;
                    hz = cam_z + best_t * dz;
                    auto __tuple_7 = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                    nx = std::get<0>(__tuple_7);
                    ny = std::get<1>(__tuple_7);
                    nz = std::get<2>(__tuple_7);
                    
                    
                    auto __tuple_8 = reflect(dx, dy, dz, nx, ny, nz);
                    rdx = std::get<0>(__tuple_8);
                    rdy = std::get<1>(__tuple_8);
                    rdz = std::get<2>(__tuple_8);
                    auto __tuple_9 = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                    tdx = std::get<0>(__tuple_9);
                    tdy = std::get<1>(__tuple_9);
                    tdz = std::get<2>(__tuple_9);
                    auto __tuple_10 = sky_color(rdx, rdy, rdz, tphase);
                    sr = std::get<0>(__tuple_10);
                    sg = std::get<1>(__tuple_10);
                    sb = std::get<2>(__tuple_10);
                    auto __tuple_11 = sky_color(tdx, tdy, tdz, tphase + 0.8);
                    tr = std::get<0>(__tuple_11);
                    tg = std::get<1>(__tuple_11);
                    tb = std::get<2>(__tuple_11);
                    cosi = std::max<float64>(static_cast<float64>(-dx * nx + dy * ny + dz * nz), static_cast<float64>(0.0));
                    fr = schlick(cosi, 0.04);
                    r = tr * (1.0 - fr) + sr * fr;
                    g = tg * (1.0 - fr) + sg * fr;
                    b = tb * (1.0 - fr) + sb * fr;
                    
                    lxv = lx - hx;
                    lyv = ly - hy;
                    lzv = lz - hz;
                    auto __tuple_12 = normalize(lxv, lyv, lzv);
                    ldx = std::get<0>(__tuple_12);
                    ldy = std::get<1>(__tuple_12);
                    ldz = std::get<2>(__tuple_12);
                    ndotl = std::max<float64>(static_cast<float64>(nx * ldx + ny * ldy + nz * ldz), static_cast<float64>(0.0));
                    auto __tuple_13 = normalize(ldx - dx, ldy - dy, ldz - dz);
                    hvx = std::get<0>(__tuple_13);
                    hvy = std::get<1>(__tuple_13);
                    hvz = std::get<2>(__tuple_13);
                    ndoth = std::max<float64>(static_cast<float64>(nx * hvx + ny * hvy + nz * hvz), static_cast<float64>(0.0));
                    spec = ndoth * ndoth;
                    spec = spec * spec;
                    spec = spec * spec;
                    spec = spec * spec;
                    glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                    r += 0.2 * ndotl + 0.8 * spec + 0.45 * glow;
                    g += 0.18 * ndotl + 0.6 * spec + 0.35 * glow;
                    b += 0.26 * ndotl + 1.0 * spec + 0.65 * glow;
                    
                    
                    if (hit_kind == 2) {
                        r *= 0.95;
                        g *= 1.05;
                        b *= 1.1;
                    } else {
                        if (hit_kind == 3) {
                            r *= 1.08;
                            g *= 0.98;
                            b *= 1.04;
                        } else {
                            r *= 1.02;
                            g *= 1.1;
                            b *= 0.95;
                        }
                    }
                }
            }
            
            
            r = py_math::sqrt(clamp01(r));
            g = py_math::sqrt(clamp01(g));
            b = py_math::sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i++;
        }
    }
    
    return list<uint8>(frame);
}

void run_16_glass_sculpture_chaos() {
    int64 width = 320;
    int64 height = 240;
    int64 frames_n = 72;
    str out_path = "sample/out/16_glass_sculpture_chaos.gif";
    
    float64 start = perf_counter();
    list<list<uint8>> frames = list<list<uint8>>{};
    for (int64 i = 0; i < frames_n; ++i)
        frames.push_back(render_frame(width, height, i, frames_n));
    
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    float64 elapsed = perf_counter() - start;
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_16_glass_sculpture_chaos();
    return 0;
}
