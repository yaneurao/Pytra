using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using math = Pytra.CsModule.math;

public static class Program
{
    // 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.
    
    public static double clamp01(double v)
    {
        if (v < 0.0) {
            return 0.0;
        }
        if (v > 1.0) {
            return 1.0;
        }
        return v;
    }
    
    public static double dot(double ax, double ay, double az, double bx, double by, double bz)
    {
        return ax * bx + ay * by + az * bz;
    }
    
    public static double length(double x, double y, double z)
    {
        return Pytra.CsModule.math.sqrt(x * x + y * y + z * z);
    }
    
    public static (double, double, double) normalize(double x, double y, double z)
    {
        double l = length(x, y, z);
        if (l < 1e-9) {
            return (0.0, 0.0, 0.0);
        }
        return (x / l, y / l, z / l);
    }
    
    public static (double, double, double) reflect(double ix, double iy, double iz, double nx, double ny, double nz)
    {
        double d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
        return (ix - d * nx, iy - d * ny, iz - d * nz);
    }
    
    public static (double, double, double) refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
    {
        // Simple IOR-based refraction. Return reflection direction on total internal reflection.
        double cosi = -dot(ix, iy, iz, nx, ny, nz);
        double sint2 = eta * eta * (1.0 - cosi * cosi);
        if (sint2 > 1.0) {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        var cost = Pytra.CsModule.math.sqrt(1.0 - sint2);
        var k = eta * cosi - cost;
        return (eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
    }
    
    public static double schlick(double cos_theta, double f0)
    {
        double m = 1.0 - cos_theta;
        return f0 + (1.0 - f0) * m * m * m * m * m;
    }
    
    public static (double, double, double) sky_color(double dx, double dy, double dz, double tphase)
    {
        // Sky gradient + neon band
        double t = 0.5 * (dy + 1.0);
        double r = 0.06 + 0.20 * t;
        double g = 0.10 + 0.25 * t;
        double b = 0.16 + 0.45 * t;
        var band = 0.5 + 0.5 * Pytra.CsModule.math.sin(8.0 * dx + 6.0 * dz + tphase);
        r += System.Convert.ToDouble(0.08 * band);
        g += System.Convert.ToDouble(0.05 * band);
        b += System.Convert.ToDouble(0.12 * band);
        return (clamp01(r), clamp01(g), clamp01(b));
    }
    
    public static double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
    {
        double lx = ox - cx;
        double ly = oy - cy;
        double lz = oz - cz;
        double b = lx * dx + ly * dy + lz * dz;
        double c = lx * lx + ly * ly + lz * lz - radius * radius;
        double h = b * b - c;
        if (h < 0.0) {
            return -1.0;
        }
        var s = Pytra.CsModule.math.sqrt(h);
        var t0 = -b - s;
        if (t0 > 1e-4) {
            return t0;
        }
        var t1 = -b + s;
        if (t1 > 1e-4) {
            return t1;
        }
        return -1.0;
    }
    
    public static List<byte> palette_332()
    {
        // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
        List<byte> p = Pytra.CsModule.py_runtime.py_bytearray(256 * 3);
        double __hoisted_cast_1 = System.Convert.ToDouble(7);
        double __hoisted_cast_2 = System.Convert.ToDouble(3);
        long i = 0;
        for (i = 0; i < 256; i += 1) {
            long r = i >> 5 & 7;
            long g = i >> 2 & 7;
            long b = i & 3;
            Pytra.CsModule.py_runtime.py_set(p, i * 3 + 0, Pytra.CsModule.py_runtime.py_int(255 * r / __hoisted_cast_1));
            Pytra.CsModule.py_runtime.py_set(p, i * 3 + 1, Pytra.CsModule.py_runtime.py_int(255 * g / __hoisted_cast_1));
            Pytra.CsModule.py_runtime.py_set(p, i * 3 + 2, Pytra.CsModule.py_runtime.py_int(255 * b / __hoisted_cast_2));
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }
    
    public static long quantize_332(double r, double g, double b)
    {
        long rr = Pytra.CsModule.py_runtime.py_int(clamp01(r) * 255.0);
        long gg = Pytra.CsModule.py_runtime.py_int(clamp01(g) * 255.0);
        long bb = Pytra.CsModule.py_runtime.py_int(clamp01(b) * 255.0);
        return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
    }
    
    public static List<byte> render_frame(long width, long height, long frame_id, long frames_n)
    {
        double t = frame_id / frames_n;
        var tphase = 2.0 * Pytra.CsModule.math.pi * t;
        
        // Camera slowly orbits.
        double cam_r = 3.0;
        var cam_x = cam_r * Pytra.CsModule.math.cos(tphase * 0.9);
        var cam_y = 1.1 + 0.25 * Pytra.CsModule.math.sin(tphase * 0.6);
        var cam_z = cam_r * Pytra.CsModule.math.sin(tphase * 0.9);
        double look_x = 0.0;
        double look_y = 0.35;
        double look_z = 0.0;
        
        var __tmp_1 = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
        var fwd_x = __tmp_1.Item1;
        var fwd_y = __tmp_1.Item2;
        var fwd_z = __tmp_1.Item3;
        var __tmp_2 = normalize(fwd_z, 0.0, -fwd_x);
        var right_x = __tmp_2.Item1;
        var right_y = __tmp_2.Item2;
        var right_z = __tmp_2.Item3;
        var __tmp_3 = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
        var up_x = __tmp_3.Item1;
        var up_y = __tmp_3.Item2;
        var up_z = __tmp_3.Item3;
        
        // Moving glass sculpture (3 spheres) and an emissive sphere.
        var s0x = 0.9 * Pytra.CsModule.math.cos(1.3 * tphase);
        var s0y = 0.15 + 0.35 * Pytra.CsModule.math.sin(1.7 * tphase);
        var s0z = 0.9 * Pytra.CsModule.math.sin(1.3 * tphase);
        var s1x = 1.2 * Pytra.CsModule.math.cos(1.3 * tphase + 2.094);
        var s1y = 0.10 + 0.40 * Pytra.CsModule.math.sin(1.1 * tphase + 0.8);
        var s1z = 1.2 * Pytra.CsModule.math.sin(1.3 * tphase + 2.094);
        var s2x = 1.0 * Pytra.CsModule.math.cos(1.3 * tphase + 4.188);
        var s2y = 0.20 + 0.30 * Pytra.CsModule.math.sin(1.5 * tphase + 1.9);
        var s2z = 1.0 * Pytra.CsModule.math.sin(1.3 * tphase + 4.188);
        double lr = 0.35;
        var lx = 2.4 * Pytra.CsModule.math.cos(tphase * 1.8);
        var ly = 1.8 + 0.8 * Pytra.CsModule.math.sin(tphase * 1.2);
        var lz = 2.4 * Pytra.CsModule.math.sin(tphase * 1.8);
        
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(width * height);
        double aspect = width / height;
        double fov = 1.25;
        double __hoisted_cast_3 = System.Convert.ToDouble(height);
        double __hoisted_cast_4 = System.Convert.ToDouble(width);
        
        long py = 0;
        for (py = 0; py < height; py += 1) {
            long row_base = py * width;
            double sy = 1.0 - 2.0 * (py + 0.5) / __hoisted_cast_3;
            long px = 0;
            for (px = 0; px < width; px += 1) {
                double sx = (2.0 * (px + 0.5) / __hoisted_cast_4 - 1.0) * aspect;
                var rx = fwd_x + fov * (sx * right_x + sy * up_x);
                var ry = fwd_y + fov * (sx * right_y + sy * up_y);
                var rz = fwd_z + fov * (sx * right_z + sy * up_z);
                var __tmp_4 = normalize(rx, ry, rz);
                var dx = __tmp_4.Item1;
                var dy = __tmp_4.Item2;
                var dz = __tmp_4.Item3;
                
                // Search for the nearest hit.
                double best_t = 1e9;
                long hit_kind = 0;
                double r = 0.0;
                double g = 0.0;
                double b = 0.0;
                
                // Floor plane y=-1.2
                if (dy < -1e-6) {
                    var tf = (-1.2 - cam_y) / dy;
                    if ((tf > 1e-4) && (tf < best_t)) {
                        best_t = System.Convert.ToDouble(tf);
                        hit_kind = 1;
                    }
                }
                double t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if ((t0 > 0.0) && (t0 < best_t)) {
                    best_t = t0;
                    hit_kind = 2;
                }
                double t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if ((t1 > 0.0) && (t1 < best_t)) {
                    best_t = t1;
                    hit_kind = 3;
                }
                double t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if ((t2 > 0.0) && (t2 < best_t)) {
                    best_t = t2;
                    hit_kind = 4;
                }
                if (hit_kind == 0) {
                    var __tmp_5 = sky_color(dx, dy, dz, tphase);
                    r = __tmp_5.Item1;
                    g = __tmp_5.Item2;
                    b = __tmp_5.Item3;
                } else {
                    if (hit_kind == 1) {
                        var hx = cam_x + best_t * dx;
                        var hz = cam_z + best_t * dz;
                        long cx = Pytra.CsModule.py_runtime.py_int(Pytra.CsModule.math.floor(hx * 2.0));
                        long cz = Pytra.CsModule.py_runtime.py_int(Pytra.CsModule.math.floor(hz * 2.0));
                        long checker = ((cx + cz) % 2 == 0 ? 0 : 1);
                        double base_r = (checker == 0 ? 0.10 : 0.04);
                        double base_g = (checker == 0 ? 0.11 : 0.05);
                        double base_b = (checker == 0 ? 0.13 : 0.08);
                        // Emissive sphere contribution.
                        var lxv = lx - hx;
                        var lyv = ly - -1.2;
                        var lzv = lz - hz;
                        var __tmp_6 = normalize(lxv, lyv, lzv);
                        var ldx = __tmp_6.Item1;
                        var ldy = __tmp_6.Item2;
                        var ldz = __tmp_6.Item3;
                        var ndotl = System.Math.Max(ldy, 0.0);
                        var ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                        var glow = 8.0 / (1.0 + ldist2);
                        r = System.Convert.ToDouble(base_r + 0.8 * glow + 0.20 * ndotl);
                        g = System.Convert.ToDouble(base_g + 0.5 * glow + 0.18 * ndotl);
                        b = System.Convert.ToDouble(base_b + 1.0 * glow + 0.24 * ndotl);
                    } else {
                        double cx = 0.0;
                        double cy = 0.0;
                        double cz = 0.0;
                        double rad = 1.0;
                        if (hit_kind == 2) {
                            cx = System.Convert.ToDouble(s0x);
                            cy = System.Convert.ToDouble(s0y);
                            cz = System.Convert.ToDouble(s0z);
                            rad = 0.65;
                        } else {
                            if (hit_kind == 3) {
                                cx = System.Convert.ToDouble(s1x);
                                cy = System.Convert.ToDouble(s1y);
                                cz = System.Convert.ToDouble(s1z);
                                rad = 0.72;
                            } else {
                                cx = System.Convert.ToDouble(s2x);
                                cy = System.Convert.ToDouble(s2y);
                                cz = System.Convert.ToDouble(s2z);
                                rad = 0.58;
                            }
                        }
                        var hx = cam_x + best_t * dx;
                        var hy = cam_y + best_t * dy;
                        var hz = cam_z + best_t * dz;
                        var __tmp_7 = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                        var nx = __tmp_7.Item1;
                        var ny = __tmp_7.Item2;
                        var nz = __tmp_7.Item3;
                        
                        // Simple glass shading (reflection + refraction + light highlights).
                        var __tmp_8 = reflect(dx, dy, dz, nx, ny, nz);
                        var rdx = __tmp_8.Item1;
                        var rdy = __tmp_8.Item2;
                        var rdz = __tmp_8.Item3;
                        var __tmp_9 = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                        var tdx = __tmp_9.Item1;
                        var tdy = __tmp_9.Item2;
                        var tdz = __tmp_9.Item3;
                        var __tmp_10 = sky_color(rdx, rdy, rdz, tphase);
                        var sr = __tmp_10.Item1;
                        var sg = __tmp_10.Item2;
                        var sb = __tmp_10.Item3;
                        var __tmp_11 = sky_color(tdx, tdy, tdz, tphase + 0.8);
                        var tr = __tmp_11.Item1;
                        var tg = __tmp_11.Item2;
                        var tb = __tmp_11.Item3;
                        var cosi = System.Math.Max(-(dx * nx + dy * ny + dz * nz), 0.0);
                        double fr = schlick(cosi, 0.04);
                        r = System.Convert.ToDouble(tr * (1.0 - fr) + sr * fr);
                        g = System.Convert.ToDouble(tg * (1.0 - fr) + sg * fr);
                        b = System.Convert.ToDouble(tb * (1.0 - fr) + sb * fr);
                        
                        var lxv = lx - hx;
                        var lyv = ly - hy;
                        var lzv = lz - hz;
                        var __tmp_12 = normalize(lxv, lyv, lzv);
                        var ldx = __tmp_12.Item1;
                        var ldy = __tmp_12.Item2;
                        var ldz = __tmp_12.Item3;
                        var ndotl = System.Math.Max(nx * ldx + ny * ldy + nz * ldz, 0.0);
                        var __tmp_13 = normalize(ldx - dx, ldy - dy, ldz - dz);
                        var hvx = __tmp_13.Item1;
                        var hvy = __tmp_13.Item2;
                        var hvz = __tmp_13.Item3;
                        var ndoth = System.Math.Max(nx * hvx + ny * hvy + nz * hvz, 0.0);
                        var spec = ndoth * ndoth;
                        spec = spec * spec;
                        spec = spec * spec;
                        spec = spec * spec;
                        var glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                        r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow;
                        g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow;
                        b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow;
                        
                        // Slight tint variation per sphere.
                        if (hit_kind == 2) {
                            r *= 0.95;
                            g *= 1.05;
                            b *= 1.10;
                        } else {
                            if (hit_kind == 3) {
                                r *= 1.08;
                                g *= 0.98;
                                b *= 1.04;
                            } else {
                                r *= 1.02;
                                g *= 1.10;
                                b *= 0.95;
                            }
                        }
                    }
                }
                // Slightly stronger tone mapping.
                r = System.Convert.ToDouble(Pytra.CsModule.math.sqrt(clamp01(r)));
                g = System.Convert.ToDouble(Pytra.CsModule.math.sqrt(clamp01(g)));
                b = System.Convert.ToDouble(Pytra.CsModule.math.sqrt(clamp01(b)));
                Pytra.CsModule.py_runtime.py_set(frame, row_base + px, quantize_332(r, g, b));
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_16_glass_sculpture_chaos()
    {
        long width = 320;
        long height = 240;
        long frames_n = 72;
        string out_path = "sample/out/16_glass_sculpture_chaos.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        long i = 0;
        for (i = 0; i < frames_n; i += 1) {
            frames.Add(render_frame(width, height, i, frames_n));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, palette_332());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_16_glass_sculpture_chaos();
    }
}
