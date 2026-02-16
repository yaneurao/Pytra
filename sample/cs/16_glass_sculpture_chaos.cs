using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static double clamp01(double v)
    {
        if (Pytra.CsModule.py_runtime.py_bool((v < 0.0)))
        {
            return 0.0;
        }
        if (Pytra.CsModule.py_runtime.py_bool((v > 1.0)))
        {
            return 1.0;
        }
        return v;
    }

    public static double dot(double ax, double ay, double az, double bx, double by, double bz)
    {
        return (((ax * bx) + (ay * by)) + (az * bz));
    }

    public static double length(double x, double y, double z)
    {
        return Math.Sqrt((((x * x) + (y * y)) + (z * z)));
    }

    public static Tuple<double, double, double> normalize(double x, double y, double z)
    {
        var l = length(x, y, z);
        if (Pytra.CsModule.py_runtime.py_bool((l < 1e-09)))
        {
            return Tuple.Create(0.0, 0.0, 0.0);
        }
        return Tuple.Create(((double)(x) / (double)(l)), ((double)(y) / (double)(l)), ((double)(z) / (double)(l)));
    }

    public static Tuple<double, double, double> reflect(double ix, double iy, double iz, double nx, double ny, double nz)
    {
        var d = (dot(ix, iy, iz, nx, ny, nz) * 2.0);
        return Tuple.Create((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)));
    }

    public static Tuple<double, double, double> refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
    {
        var cosi = (-dot(ix, iy, iz, nx, ny, nz));
        var sint2 = ((eta * eta) * (1.0 - (cosi * cosi)));
        if (Pytra.CsModule.py_runtime.py_bool((sint2 > 1.0)))
        {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        var cost = Math.Sqrt((1.0 - sint2));
        var k = ((eta * cosi) - cost);
        return Tuple.Create(((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)));
    }

    public static double schlick(double cos_theta, double f0)
    {
        var m = (1.0 - cos_theta);
        return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)));
    }

    public static Tuple<double, double, double> sky_color(double dx, double dy, double dz, double tphase)
    {
        var t = (0.5 * (dy + 1.0));
        var r = (0.06 + (0.2 * t));
        var g = (0.1 + (0.25 * t));
        var b = (0.16 + (0.45 * t));
        var band = (0.5 + (0.5 * Math.Sin((((8.0 * dx) + (6.0 * dz)) + tphase))));
        r = (r + (0.08 * band));
        g = (g + (0.05 * band));
        b = (b + (0.12 * band));
        return Tuple.Create(clamp01(r), clamp01(g), clamp01(b));
    }

    public static double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
    {
        var lx = (ox - cx);
        var ly = (oy - cy);
        var lz = (oz - cz);
        var b = (((lx * dx) + (ly * dy)) + (lz * dz));
        var c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius));
        var h = ((b * b) - c);
        if (Pytra.CsModule.py_runtime.py_bool((h < 0.0)))
        {
            return (-1.0);
        }
        var s = Math.Sqrt(h);
        var t0 = ((-b) - s);
        if (Pytra.CsModule.py_runtime.py_bool((t0 > 0.0001)))
        {
            return t0;
        }
        var t1 = ((-b) + s);
        if (Pytra.CsModule.py_runtime.py_bool((t1 > 0.0001)))
        {
            return t1;
        }
        return (-1.0);
    }

    public static List<byte> palette_332()
    {
        var p = Pytra.CsModule.py_runtime.py_bytearray((256L * 3L));
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = ((i >> (int)(5L)) & 7L);
            var g = ((i >> (int)(2L)) & 7L);
            var b = (i & 3L);
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 0L), (long)(((double)((255L * r)) / (double)(7L))));
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 1L), (long)(((double)((255L * g)) / (double)(7L))));
            Pytra.CsModule.py_runtime.py_set(p, ((i * 3L) + 2L), (long)(((double)((255L * b)) / (double)(3L))));
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }

    public static long quantize_332(double r, double g, double b)
    {
        var rr = (long)((clamp01(r) * 255.0));
        var gg = (long)((clamp01(g) * 255.0));
        var bb = (long)((clamp01(b) * 255.0));
        return ((((rr >> (int)(5L)) << (int)(5L)) + ((gg >> (int)(5L)) << (int)(2L))) + (bb >> (int)(6L)));
    }

    public static List<byte> render_frame(long width, long height, long frame_id, long frames_n)
    {
        var t = ((double)(frame_id) / (double)(frames_n));
        var tphase = ((2.0 * Math.PI) * t);
        double cam_r = 3.0;
        var cam_x = (cam_r * Math.Cos((tphase * 0.9)));
        var cam_y = (1.1 + (0.25 * Math.Sin((tphase * 0.6))));
        var cam_z = (cam_r * Math.Sin((tphase * 0.9)));
        double look_x = 0.0;
        double look_y = 0.35;
        double look_z = 0.0;
        var __pytra_tuple_4 = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z));
        var fwd_x = __pytra_tuple_4.Item1;
        var fwd_y = __pytra_tuple_4.Item2;
        var fwd_z = __pytra_tuple_4.Item3;
        var __pytra_tuple_5 = normalize(fwd_z, 0.0, (-fwd_x));
        var right_x = __pytra_tuple_5.Item1;
        var right_y = __pytra_tuple_5.Item2;
        var right_z = __pytra_tuple_5.Item3;
        var __pytra_tuple_6 = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)));
        var up_x = __pytra_tuple_6.Item1;
        var up_y = __pytra_tuple_6.Item2;
        var up_z = __pytra_tuple_6.Item3;
        var s0x = (0.9 * Math.Cos((1.3 * tphase)));
        var s0y = (0.15 + (0.35 * Math.Sin((1.7 * tphase))));
        var s0z = (0.9 * Math.Sin((1.3 * tphase)));
        var s1x = (1.2 * Math.Cos(((1.3 * tphase) + 2.094)));
        var s1y = (0.1 + (0.4 * Math.Sin(((1.1 * tphase) + 0.8))));
        var s1z = (1.2 * Math.Sin(((1.3 * tphase) + 2.094)));
        var s2x = (1.0 * Math.Cos(((1.3 * tphase) + 4.188)));
        var s2y = (0.2 + (0.3 * Math.Sin(((1.5 * tphase) + 1.9))));
        var s2z = (1.0 * Math.Sin(((1.3 * tphase) + 4.188)));
        double lr = 0.35;
        var lx = (2.4 * Math.Cos((tphase * 1.8)));
        var ly = (1.8 + (0.8 * Math.Sin((tphase * 1.2))));
        var lz = (2.4 * Math.Sin((tphase * 1.8)));
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
        var aspect = ((double)(width) / (double)(height));
        double fov = 1.25;
        long i = 0L;
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = height;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var py = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (py < __pytra_range_stop_8) : (py > __pytra_range_stop_8); py += __pytra_range_step_9)
        {
            var sy = (1.0 - ((double)((2.0 * (py + 0.5))) / (double)(height)));
            var __pytra_range_start_10 = 0;
            var __pytra_range_stop_11 = width;
            var __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var px = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (px < __pytra_range_stop_11) : (px > __pytra_range_stop_11); px += __pytra_range_step_12)
            {
                var sx = ((((double)((2.0 * (px + 0.5))) / (double)(width)) - 1.0) * aspect);
                var rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))));
                var ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))));
                var rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))));
                var __pytra_tuple_13 = normalize(rx, ry, rz);
                var dx = __pytra_tuple_13.Item1;
                var dy = __pytra_tuple_13.Item2;
                var dz = __pytra_tuple_13.Item3;
                double best_t = 1000000000.0;
                long hit_kind = 0L;
                double r = 0.0;
                double g = 0.0;
                double b = 0.0;
                if (Pytra.CsModule.py_runtime.py_bool((dy < (-1e-06))))
                {
                    var tf = ((double)(((-1.2) - cam_y)) / (double)(dy));
                    if (Pytra.CsModule.py_runtime.py_bool(((tf > 0.0001) && (tf < best_t))))
                    {
                        best_t = tf;
                        hit_kind = 1L;
                    }
                }
                var t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if (Pytra.CsModule.py_runtime.py_bool(((t0 > 0.0) && (t0 < best_t))))
                {
                    best_t = t0;
                    hit_kind = 2L;
                }
                var t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if (Pytra.CsModule.py_runtime.py_bool(((t1 > 0.0) && (t1 < best_t))))
                {
                    best_t = t1;
                    hit_kind = 3L;
                }
                var t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if (Pytra.CsModule.py_runtime.py_bool(((t2 > 0.0) && (t2 < best_t))))
                {
                    best_t = t2;
                    hit_kind = 4L;
                }
                if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 0L)))
                {
                    var __pytra_tuple_14 = sky_color(dx, dy, dz, tphase);
                    r = __pytra_tuple_14.Item1;
                    g = __pytra_tuple_14.Item2;
                    b = __pytra_tuple_14.Item3;
                }
                else
                {
                    if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 1L)))
                    {
                        var hx = (cam_x + (best_t * dx));
                        var hz = (cam_z + (best_t * dz));
                        var cx = (long)(Math.Floor((hx * 2.0)));
                        var cz = (long)(Math.Floor((hz * 2.0)));
                        var checker = (Pytra.CsModule.py_runtime.py_bool((((cx + cz) % 2L) == 0L)) ? 0L : 1L);
                        var base_r = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.1 : 0.04);
                        var base_g = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.11 : 0.05);
                        var base_b = (Pytra.CsModule.py_runtime.py_bool((checker == 0L)) ? 0.13 : 0.08);
                        var lxv = (lx - hx);
                        var lyv = (ly - (-1.2));
                        var lzv = (lz - hz);
                        var __pytra_tuple_15 = normalize(lxv, lyv, lzv);
                        var ldx = __pytra_tuple_15.Item1;
                        var ldy = __pytra_tuple_15.Item2;
                        var ldz = __pytra_tuple_15.Item3;
                        var ndotl = ((ldy) > (0.0) ? (ldy) : (0.0));
                        var ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv));
                        var glow = ((double)(8.0) / (double)((1.0 + ldist2)));
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
                        if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 2L)))
                        {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        }
                        else
                        {
                            if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 3L)))
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
                        var hx = (cam_x + (best_t * dx));
                        var hy = (cam_y + (best_t * dy));
                        var hz = (cam_z + (best_t * dz));
                        var __pytra_tuple_16 = normalize(((double)((hx - cx)) / (double)(rad)), ((double)((hy - cy)) / (double)(rad)), ((double)((hz - cz)) / (double)(rad)));
                        var nx = __pytra_tuple_16.Item1;
                        var ny = __pytra_tuple_16.Item2;
                        var nz = __pytra_tuple_16.Item3;
                        var __pytra_tuple_17 = reflect(dx, dy, dz, nx, ny, nz);
                        var rdx = __pytra_tuple_17.Item1;
                        var rdy = __pytra_tuple_17.Item2;
                        var rdz = __pytra_tuple_17.Item3;
                        var __pytra_tuple_18 = refract(dx, dy, dz, nx, ny, nz, ((double)(1.0) / (double)(1.45)));
                        var tdx = __pytra_tuple_18.Item1;
                        var tdy = __pytra_tuple_18.Item2;
                        var tdz = __pytra_tuple_18.Item3;
                        var __pytra_tuple_19 = sky_color(rdx, rdy, rdz, tphase);
                        var sr = __pytra_tuple_19.Item1;
                        var sg = __pytra_tuple_19.Item2;
                        var sb = __pytra_tuple_19.Item3;
                        var __pytra_tuple_20 = sky_color(tdx, tdy, tdz, (tphase + 0.8));
                        var tr = __pytra_tuple_20.Item1;
                        var tg = __pytra_tuple_20.Item2;
                        var tb = __pytra_tuple_20.Item3;
                        var cosi = (((-(((dx * nx) + (dy * ny)) + (dz * nz)))) > (0.0) ? ((-(((dx * nx) + (dy * ny)) + (dz * nz)))) : (0.0));
                        var fr = schlick(cosi, 0.04);
                        r = ((tr * (1.0 - fr)) + (sr * fr));
                        g = ((tg * (1.0 - fr)) + (sg * fr));
                        b = ((tb * (1.0 - fr)) + (sb * fr));
                        var lxv = (lx - hx);
                        var lyv = (ly - hy);
                        var lzv = (lz - hz);
                        var __pytra_tuple_21 = normalize(lxv, lyv, lzv);
                        var ldx = __pytra_tuple_21.Item1;
                        var ldy = __pytra_tuple_21.Item2;
                        var ldz = __pytra_tuple_21.Item3;
                        var ndotl = (((((nx * ldx) + (ny * ldy)) + (nz * ldz))) > (0.0) ? ((((nx * ldx) + (ny * ldy)) + (nz * ldz))) : (0.0));
                        var __pytra_tuple_22 = normalize((ldx - dx), (ldy - dy), (ldz - dz));
                        var hvx = __pytra_tuple_22.Item1;
                        var hvy = __pytra_tuple_22.Item2;
                        var hvz = __pytra_tuple_22.Item3;
                        var ndoth = (((((nx * hvx) + (ny * hvy)) + (nz * hvz))) > (0.0) ? ((((nx * hvx) + (ny * hvy)) + (nz * hvz))) : (0.0));
                        var spec = (ndoth * ndoth);
                        spec = (spec * spec);
                        spec = (spec * spec);
                        spec = (spec * spec);
                        var glow = ((double)(10.0) / (double)((((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv))));
                        r = (r + (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow)));
                        g = (g + (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow)));
                        b = (b + (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow)));
                        if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 2L)))
                        {
                            r = (r * 0.95);
                            g = (g * 1.05);
                            b = (b * 1.1);
                        }
                        else
                        {
                            if (Pytra.CsModule.py_runtime.py_bool((hit_kind == 3L)))
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
                r = Math.Sqrt(clamp01(r));
                g = Math.Sqrt(clamp01(g));
                b = Math.Sqrt(clamp01(b));
                Pytra.CsModule.py_runtime.py_set(frame, i, quantize_332(r, g, b));
                i = (i + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_16_glass_sculpture_chaos()
    {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        string out_path = "sample/out/16_glass_sculpture_chaos.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_23 = 0;
        var __pytra_range_stop_24 = frames_n;
        var __pytra_range_step_25 = 1;
        if (__pytra_range_step_25 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_23; (__pytra_range_step_25 > 0) ? (i < __pytra_range_stop_24) : (i > __pytra_range_stop_24); i += __pytra_range_step_25)
        {
            Pytra.CsModule.py_runtime.py_append(frames, render_frame(width, height, i, frames_n));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, palette_332(), delay_cs: 6L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_16_glass_sculpture_chaos();
    }
}
