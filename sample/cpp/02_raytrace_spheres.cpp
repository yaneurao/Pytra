#include "cpp_module/py_runtime.h"

// 02: 球のみのミニレイトレーサを実行し、PNG画像を出力するサンプルです。
// トランスパイル互換のため、依存モジュールは最小限（timeのみ）にしています。

float64 clamp01(float64 v) {
    if (v < 0.0)
        return 0.0;
    if (v > 1.0)
        return 1.0;
    return v;
}

float64 hit_sphere(float64 ox, float64 oy, float64 oz, float64 dx, float64 dy, float64 dz, float64 cx, float64 cy, float64 cz, float64 r) {
    // レイと球の交差距離t（交差しない場合は-1）を返す。
    float64 lx = ox - cx;
    float64 ly = oy - cy;
    float64 lz = oz - cz;
    
    float64 a = dx * dx + dy * dy + dz * dz;
    float64 b = 2.0 * (lx * dx + ly * dy + lz * dz);
    float64 c = lx * lx + ly * ly + lz * lz - r * r;
    
    float64 d = b * b - 4.0 * a * c;
    if (d < 0.0)
        return -1.0;
    
    float64 sd = py_math::sqrt(d);
    float64 t0 = (-b - sd) / (2.0 * a);
    float64 t1 = (-b + sd) / (2.0 * a);
    
    if (t0 > 0.001)
        return t0;
    if (t1 > 0.001)
        return t1;
    return -1.0;
}

bytearray render(int64 width, int64 height, int64 aa) {
    bytearray pixels = bytearray{};
    
    // カメラ原点
    float64 ox = 0.0;
    float64 oy = 0.0;
    float64 oz = -3.0;
    
    // ライト方向（正規化済み）
    float64 lx = -0.4;
    float64 ly = 0.8;
    float64 lz = -0.45;
    
    for (int64 y = 0; y < height; ++y) {
        for (int64 x = 0; x < width; ++x) {
            int64 ar = 0;
            int64 ag = 0;
            int64 ab = 0;
            
            for (int64 ay = 0; ay < aa; ++ay) {
                for (int64 ax = 0; ax < aa; ++ax) {
                    float64 fy = (static_cast<float64>(y) + (static_cast<float64>(ay) + 0.5) / static_cast<float64>(aa)) / (static_cast<float64>(height - 1));
                    float64 fx = (static_cast<float64>(x) + (static_cast<float64>(ax) + 0.5) / static_cast<float64>(aa)) / (static_cast<float64>(width - 1));
                    float64 sy = 1.0 - 2.0 * fy;
                    float64 sx = (2.0 * fx - 1.0) * (static_cast<float64>(width) / static_cast<float64>(height));
                    
                    float64 dx = sx;
                    float64 dy = sy;
                    float64 dz = 1.0;
                    float64 inv_len = 1.0 / py_math::sqrt(dx * dx + dy * dy + dz * dz);
                    dx *= inv_len;
                    dy *= inv_len;
                    dz *= inv_len;
                    
                    float64 t_min = 1e+30;
                    int64 hit_id = -1;
                    
                    float64 t = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t;
                        hit_id = 0;
                    }
                    
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t;
                        hit_id = 1;
                    }
                    
                    t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
                    if ((t > 0.0) && (t < t_min)) {
                        t_min = t;
                        hit_id = 2;
                    }
                    
                    int64 r = 0;
                    int64 g = 0;
                    int64 b = 0;
                    
                    if (hit_id >= 0) {
                        float64 px = ox + dx * t_min;
                        float64 py = oy + dy * t_min;
                        float64 pz = oz + dz * t_min;
                        
                        float64 nx = 0.0;
                        float64 ny = 0.0;
                        float64 nz = 0.0;
                        
                        if (hit_id == 0) {
                            nx = (px + 0.8) / 0.8;
                            ny = (py + 0.2) / 0.8;
                            nz = (pz - 2.2) / 0.8;
                        } else {
                            if (hit_id == 1) {
                                nx = (px - 0.9) / 0.95;
                                ny = (py - 0.1) / 0.95;
                                nz = (pz - 2.9) / 0.95;
                            } else {
                                nx = 0.0;
                                ny = 1.0;
                                nz = 0.0;
                            }
                        }
                        
                        float64 diff = nx * -lx + ny * -ly + nz * -lz;
                        diff = clamp01(diff);
                        
                        float64 base_r = 0.0;
                        float64 base_g = 0.0;
                        float64 base_b = 0.0;
                        
                        if (hit_id == 0) {
                            base_r = 0.95;
                            base_g = 0.35;
                            base_b = 0.25;
                        } else {
                            if (hit_id == 1) {
                                base_r = 0.25;
                                base_g = 0.55;
                                base_b = 0.95;
                            } else {
                                int64 checker = int64((px + 50.0) * 0.8) + int64((pz + 50.0) * 0.8);
                                if (checker % 2 == 0) {
                                    base_r = 0.85;
                                    base_g = 0.85;
                                    base_b = 0.85;
                                } else {
                                    base_r = 0.2;
                                    base_g = 0.2;
                                    base_b = 0.2;
                                }
                            }
                        }
                        
                        float64 shade = 0.12 + 0.88 * diff;
                        r = int64(255.0 * clamp01(base_r * shade));
                        g = int64(255.0 * clamp01(base_g * shade));
                        b = int64(255.0 * clamp01(base_b * shade));
                    } else {
                        float64 tsky = 0.5 * (dy + 1.0);
                        r = int64(255.0 * (0.65 + 0.2 * tsky));
                        g = int64(255.0 * (0.75 + 0.18 * tsky));
                        b = int64(255.0 * (0.9 + 0.08 * tsky));
                    }
                    
                    ar += r;
                    ag += g;
                    ab += b;
                }
            }
            
            int64 samples = aa * aa;
            pixels.append(py_floordiv(ar, samples));
            pixels.append(py_floordiv(ag, samples));
            pixels.append(py_floordiv(ab, samples));
        }
    }
    
    return pixels;
}

void run_raytrace() {
    int64 width = 1600;
    int64 height = 900;
    int64 aa = 2;
    str out_path = "sample/out/raytrace_02.png";
    
    float64 start = perf_counter();
    bytearray pixels = render(width, height, aa);
    // bridge: Python png_helper.write_rgb_png -> C++ runtime png_helper::write_rgb_png
    png_helper::write_rgb_png(out_path, width, height, pixels);
    float64 elapsed = perf_counter() - start;
    
    py_print("output:", out_path);
    py_print("size:", width, "x", height);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_raytrace();
    return 0;
}
