using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static double clamp01(double v)
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

    public static double hit_sphere(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double r)
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
        double sd = Math.Sqrt(d);
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

    public static List<byte> render(int width, int height)
    {
        List<byte> pixels = new List<byte>();
        double ox = 0.0;
        double oy = 0.0;
        double oz = (-3.0);
        double lx = (-0.4);
        double ly = 0.8;
        double lz = (-0.45);
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            double sy = (1.0 - (2.0 * (y / (height - 1))));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                double sx = ((2.0 * (x / (width - 1))) - 1.0);
                sx = (sx * (width / height));
                double dx = sx;
                double dy = sy;
                double dz = 1.0;
                double inv_len = (1.0 / Math.Sqrt((((dx * dx) + (dy * dy)) + (dz * dz))));
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
                            int checker = ((int)(((px + 50.0) * 0.8)) + (int)(((pz + 50.0) * 0.8)));
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
                    r = (int)((255.0 * clamp01((base_r * shade))));
                    g = (int)((255.0 * clamp01((base_g * shade))));
                    b = (int)((255.0 * clamp01((base_b * shade))));
                }
                else
                {
                    double tsky = (0.5 * (dy + 1.0));
                    r = (int)((255.0 * (0.65 + (0.2 * tsky))));
                    g = (int)((255.0 * (0.75 + (0.18 * tsky))));
                    b = (int)((255.0 * (0.9 + (0.08 * tsky))));
                }
                pixels.Add((byte)(r));
                pixels.Add((byte)(g));
                pixels.Add((byte)(b));
            }
        }
        return pixels;
    }

    public static void run_raytrace()
    {
        int width = 960;
        int height = 540;
        string out_path = "sample/out/raytrace_02.png";
        double start = Pytra.CsModule.time.perf_counter();
        List<byte> pixels = render(width, height);
        Pytra.CsModule.png_helper.write_rgb_png(out_path, width, height, pixels);
        double elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("size:", width, "x", height);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_raytrace();
    }
}
