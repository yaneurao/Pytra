#include "cpp_module/py_runtime.h"


// 16: ガラス彫刻のカオス回転をレイトレーシングで描き、GIF出力するサンプル。

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
    // IOR 由来の簡易屈折。全反射時は反射方向を返す。
    float64 cosi = -dot(ix, iy, iz, nx, ny, nz);
    float64 sint2 = eta * eta * (1.0 - cosi * cosi);
    if (sint2 > 1.0)
        return reflect(ix, iy, iz, nx, ny, nz);
    std::any cost = make_object(py_math::sqrt(1.0 - sint2));
    std::any k = make_object(eta * cosi - cost);
    return std::make_tuple(eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
}

float64 schlick(float64 cos_theta, float64 f0) {
    float64 m = 1.0 - cos_theta;
    return f0 + (1.0 - f0) * m * m * m * m * m;
}

std::tuple<float64, float64, float64> sky_color(float64 dx, float64 dy, float64 dz, float64 tphase) {
    // 上空グラデーション + ネオン帯
    float64 t = 0.5 * (dy + 1.0);
    float64 r = 0.06 + 0.2 * t;
    float64 g = 0.1 + 0.25 * t;
    float64 b = 0.16 + 0.45 * t;
    std::any band = make_object(0.5 + 0.5 * py_math::sin(8.0 * dx + 6.0 * dz + tphase));
    r += static_cast<float64>(py_to_int64(0.08 * band));
    g += static_cast<float64>(py_to_int64(0.05 * band));
    b += static_cast<float64>(py_to_int64(0.12 * band));
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
    std::any s = make_object(py_math::sqrt(h));
    std::any t0 = make_object(-b - s);
    if (t0 > 0.0001)
        return t0;
    std::any t1 = make_object(-b + s);
    if (t1 > 0.0001)
        return t1;
    return -1.0;
}

bytes palette_332() {
    // 3-3-2 量子化パレット。量子化処理が軽く、トランスパイル後も高速。
    bytearray p = bytearray(256 * 3);
    for (int64 i = 0; i < 256; ++i) {
        int64 r = i >> 5 & 7;
        int64 g = i >> 2 & 7;
        int64 b = i & 3;
        p[i * 3 + 0] = int64(static_cast<float64>(255 * r) / static_cast<float64>(7));
        p[i * 3 + 1] = int64(static_cast<float64>(255 * g) / static_cast<float64>(7));
        p[i * 3 + 2] = int64(static_cast<float64>(255 * b) / static_cast<float64>(3));
    }
    return bytes(p);
}

int64 quantize_332(float64 r, float64 g, float64 b) {
    int64 rr = int64(clamp01(r) * 255.0);
    int64 gg = int64(clamp01(g) * 255.0);
    int64 bb = int64(clamp01(b) * 255.0);
    return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
}

bytes render_frame(int64 width, int64 height, int64 frame_id, int64 frames_n) {
    float64 t = static_cast<float64>(frame_id) / static_cast<float64>(frames_n);
    std::any tphase = make_object(2.0 * py_math::pi * t);
    
    // カメラはゆっくり周回
    float64 cam_r = 3.0;
    std::any cam_x = make_object(cam_r * py_math::cos(tphase * 0.9));
    std::any cam_y = make_object(1.1 + 0.25 * py_math::sin(tphase * 0.6));
    std::any cam_z = make_object(cam_r * py_math::sin(tphase * 0.9));
    float64 look_x = 0.0;
    float64 look_y = 0.35;
    float64 look_z = 0.0;
    
    auto __tuple_1 = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
    float64 fwd_x = std::get<0>(__tuple_1);
    float64 fwd_y = std::get<1>(__tuple_1);
    float64 fwd_z = std::get<2>(__tuple_1);
    auto __tuple_2 = normalize(fwd_z, 0.0, -fwd_x);
    float64 right_x = std::get<0>(__tuple_2);
    float64 right_y = std::get<1>(__tuple_2);
    float64 right_z = std::get<2>(__tuple_2);
    auto __tuple_3 = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
    float64 up_x = std::get<0>(__tuple_3);
    float64 up_y = std::get<1>(__tuple_3);
    float64 up_z = std::get<2>(__tuple_3);
    
    // 動くガラス彫刻（3球）と発光球
    std::any s0x = make_object(0.9 * py_math::cos(1.3 * tphase));
    std::any s0y = make_object(0.15 + 0.35 * py_math::sin(1.7 * tphase));
    std::any s0z = make_object(0.9 * py_math::sin(1.3 * tphase));
    std::any s1x = make_object(1.2 * py_math::cos(1.3 * tphase + 2.094));
    std::any s1y = make_object(0.1 + 0.4 * py_math::sin(1.1 * tphase + 0.8));
    std::any s1z = make_object(1.2 * py_math::sin(1.3 * tphase + 2.094));
    std::any s2x = make_object(1.0 * py_math::cos(1.3 * tphase + 4.188));
    std::any s2y = make_object(0.2 + 0.3 * py_math::sin(1.5 * tphase + 1.9));
    std::any s2z = make_object(1.0 * py_math::sin(1.3 * tphase + 4.188));
    float64 lr = 0.35;
    std::any lx = make_object(2.4 * py_math::cos(tphase * 1.8));
    std::any ly = make_object(1.8 + 0.8 * py_math::sin(tphase * 1.2));
    std::any lz = make_object(2.4 * py_math::sin(tphase * 1.8));
    
    bytearray frame = bytearray(width * height);
    float64 aspect = static_cast<float64>(width) / static_cast<float64>(height);
    float64 fov = 1.25;
    
    int64 i = 0;
    for (int64 py = 0; py < height; ++py) {
        float64 sy = 1.0 - 2.0 * (static_cast<float64>(py) + 0.5) / static_cast<float64>(height);
        for (int64 px = 0; px < width; ++px) {
            float64 sx = (2.0 * (static_cast<float64>(px) + 0.5) / static_cast<float64>(width) - 1.0) * aspect;
            std::any rx = make_object(fwd_x + fov * (sx * right_x + sy * up_x));
            std::any ry = make_object(fwd_y + fov * (sx * right_y + sy * up_y));
            std::any rz = make_object(fwd_z + fov * (sx * right_z + sy * up_z));
            auto __tuple_4 = normalize(rx, ry, rz);
            float64 dx = std::get<0>(__tuple_4);
            float64 dy = std::get<1>(__tuple_4);
            float64 dz = std::get<2>(__tuple_4);
            
            // 最短ヒットを探索
            float64 best_t = 1000000000.0;
            int64 hit_kind = 0;
            float64 r = 0.0;
            float64 g = 0.0;
            float64 b = 0.0;
            
            // 床平面 y=-1.2
            if (dy < -1e-06) {
                float64 tf = py_div((-1.2 - cam_y), dy);
                if ((tf > 0.0001) && (tf < best_t)) {
                    best_t = tf;
                    hit_kind = 1;
                }
            }
            
            std::any t0 = make_object(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65));
            if ((t0 > 0.0) && (t0 < best_t)) {
                best_t = t0;
                hit_kind = 2;
            }
            std::any t1 = make_object(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72));
            if ((t1 > 0.0) && (t1 < best_t)) {
                best_t = t1;
                hit_kind = 3;
            }
            std::any t2 = make_object(sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58));
            if ((t2 > 0.0) && (t2 < best_t)) {
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
                    std::any hx = make_object(cam_x + best_t * dx);
                    std::any hz = make_object(cam_z + best_t * dz);
                    int64 cx = py_to_int64(py_math::floor(hx * 2.0));
                    int64 cz = py_to_int64(py_math::floor(hz * 2.0));
                    int64 checker = ((cx + cz) % 2 == 0 ? 0 : 1);
                    float64 base_r = (checker == 0 ? 0.1 : 0.04);
                    float64 base_g = (checker == 0 ? 0.11 : 0.05);
                    float64 base_b = (checker == 0 ? 0.13 : 0.08);
                    // 発光球の寄与
                    std::any lxv = make_object(lx - hx);
                    std::any lyv = make_object(ly - -1.2);
                    std::any lzv = make_object(lz - hz);
                    auto __tuple_6 = normalize(lxv, lyv, lzv);
                    float64 ldx = std::get<0>(__tuple_6);
                    float64 ldy = std::get<1>(__tuple_6);
                    float64 ldz = std::get<2>(__tuple_6);
                    std::any ndotl = make_object(std::max<std::any>(static_cast<std::any>(ldy), static_cast<std::any>(0.0)));
                    std::any ldist2 = make_object(lxv * lxv + lyv * lyv + lzv * lzv);
                    float64 glow = 8.0 / (1.0 + ldist2);
                    r = base_r + 0.8 * glow + 0.2 * ndotl;
                    g = base_g + 0.5 * glow + 0.18 * ndotl;
                    b = base_b + 1.0 * glow + 0.24 * ndotl;
                } else {
                    float64 cx = 0.0;
                    float64 cy = 0.0;
                    float64 cz = 0.0;
                    float64 rad = 1.0;
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
                    std::any hx = make_object(cam_x + best_t * dx);
                    std::any hy = make_object(cam_y + best_t * dy);
                    std::any hz = make_object(cam_z + best_t * dz);
                    auto __tuple_7 = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                    float64 nx = std::get<0>(__tuple_7);
                    float64 ny = std::get<1>(__tuple_7);
                    float64 nz = std::get<2>(__tuple_7);
                    
                    // 簡易ガラスシェーディング（反射+屈折+光源ハイライト）
                    auto __tuple_8 = reflect(dx, dy, dz, nx, ny, nz);
                    float64 rdx = std::get<0>(__tuple_8);
                    float64 rdy = std::get<1>(__tuple_8);
                    float64 rdz = std::get<2>(__tuple_8);
                    auto __tuple_9 = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                    float64 tdx = std::get<0>(__tuple_9);
                    float64 tdy = std::get<1>(__tuple_9);
                    float64 tdz = std::get<2>(__tuple_9);
                    auto __tuple_10 = sky_color(rdx, rdy, rdz, tphase);
                    float64 sr = std::get<0>(__tuple_10);
                    float64 sg = std::get<1>(__tuple_10);
                    float64 sb = std::get<2>(__tuple_10);
                    auto __tuple_11 = sky_color(tdx, tdy, tdz, tphase + 0.8);
                    float64 tr = std::get<0>(__tuple_11);
                    float64 tg = std::get<1>(__tuple_11);
                    float64 tb = std::get<2>(__tuple_11);
                    std::any cosi = make_object(std::max<std::any>(static_cast<std::any>(-dx * nx + dy * ny + dz * nz), static_cast<std::any>(0.0)));
                    float64 fr = schlick(cosi, 0.04);
                    r = tr * (1.0 - fr) + sr * fr;
                    g = tg * (1.0 - fr) + sg * fr;
                    b = tb * (1.0 - fr) + sb * fr;
                    
                    std::any lxv = make_object(lx - hx);
                    std::any lyv = make_object(ly - hy);
                    std::any lzv = make_object(lz - hz);
                    auto __tuple_12 = normalize(lxv, lyv, lzv);
                    float64 ldx = std::get<0>(__tuple_12);
                    float64 ldy = std::get<1>(__tuple_12);
                    float64 ldz = std::get<2>(__tuple_12);
                    std::any ndotl = make_object(std::max<std::any>(static_cast<std::any>(nx * ldx + ny * ldy + nz * ldz), static_cast<std::any>(0.0)));
                    auto __tuple_13 = normalize(ldx - dx, ldy - dy, ldz - dz);
                    float64 hvx = std::get<0>(__tuple_13);
                    float64 hvy = std::get<1>(__tuple_13);
                    float64 hvz = std::get<2>(__tuple_13);
                    std::any ndoth = make_object(std::max<std::any>(static_cast<std::any>(nx * hvx + ny * hvy + nz * hvz), static_cast<std::any>(0.0)));
                    std::any spec = make_object(ndoth * ndoth);
                    spec = make_object(spec * spec);
                    spec = make_object(spec * spec);
                    spec = make_object(spec * spec);
                    float64 glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                    r += 0.2 * ndotl + 0.8 * spec + 0.45 * glow;
                    g += 0.18 * ndotl + 0.6 * spec + 0.35 * glow;
                    b += 0.26 * ndotl + 1.0 * spec + 0.65 * glow;
                    
                    // 球ごとに僅かな色味差
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
            
            // やや強めのトーンマップ
            r = py_math::sqrt(clamp01(r));
            g = py_math::sqrt(clamp01(g));
            b = py_math::sqrt(clamp01(b));
            frame[i] = quantize_332(r, g, b);
            i++;
        }
    }
    
    return bytes(frame);
}

void run_16_glass_sculpture_chaos() {
    int64 width = 320;
    int64 height = 240;
    int64 frames_n = 72;
    str out_path = "sample/out/16_glass_sculpture_chaos.gif";
    
    std::any start = make_object(perf_counter());
    list<bytes> frames = list<bytes>{};
    for (int64 i = 0; i < frames_n; ++i)
        frames.append(render_frame(width, height, i, frames_n));
    
    // bridge: Python gif.save_gif -> C++ runtime save_gif
    save_gif(out_path, width, height, frames, palette_332(), 6, 0);
    std::any elapsed = make_object(perf_counter() - start);
    py_print("output:", out_path);
    py_print("frames:", frames_n);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_16_glass_sculpture_chaos();
    return 0;
}
