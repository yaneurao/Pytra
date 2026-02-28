using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using math = Pytra.CsModule.math;

public static class Program
{
    // 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.
    
    public static List<byte> palette()
    {
        List<byte> p = new System.Collections.Generic.List<byte>();
        long i = 0;
        for (i = 0; i < 256; i += 1) {
            var r = System.Math.Min(255, Pytra.CsModule.py_runtime.py_int(20 + i * 0.9));
            var g = System.Math.Min(255, Pytra.CsModule.py_runtime.py_int(10 + i * 0.7));
            var b = System.Math.Min(255, 30 + i);
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }
    
    public static long scene(double x, double y, double light_x, double light_y)
    {
        double x1 = x + 0.45;
        double y1 = y + 0.2;
        double x2 = x - 0.35;
        double y2 = y - 0.15;
        var r1 = Pytra.CsModule.math.sqrt(x1 * x1 + y1 * y1);
        var r2 = Pytra.CsModule.math.sqrt(x2 * x2 + y2 * y2);
        var blob = Pytra.CsModule.math.exp(-7.0 * r1 * r1) + Pytra.CsModule.math.exp(-8.0 * r2 * r2);
        
        double lx = x - light_x;
        double ly = y - light_y;
        var l = Pytra.CsModule.math.sqrt(lx * lx + ly * ly);
        var lit = 1.0 / (1.0 + 3.5 * l * l);
        
        long v = Pytra.CsModule.py_runtime.py_int(255.0 * blob * lit * 5.0);
        return System.Math.Min(255, System.Math.Max(0, v));
    }
    
    public static void run_14_raymarching_light_cycle()
    {
        long w = 320;
        long h = 240;
        long frames_n = 84;
        string out_path = "sample/out/14_raymarching_light_cycle.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        double __hoisted_cast_1 = System.Convert.ToDouble(frames_n);
        double __hoisted_cast_2 = System.Convert.ToDouble(h - 1);
        double __hoisted_cast_3 = System.Convert.ToDouble(w - 1);
        
        long t = 0;
        for (t = 0; t < frames_n; t += 1) {
            List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
            var a = (t / __hoisted_cast_1) * Pytra.CsModule.math.pi * 2.0;
            var light_x = 0.75 * Pytra.CsModule.math.cos(a);
            var light_y = 0.55 * Pytra.CsModule.math.sin(a * 1.2);
            
            long y = 0;
            for (y = 0; y < h; y += 1) {
                long row_base = y * w;
                double py = (y / __hoisted_cast_2) * 2.0 - 1.0;
                long x = 0;
                for (x = 0; x < w; x += 1) {
                    double px = (x / __hoisted_cast_3) * 2.0 - 1.0;
                    Pytra.CsModule.py_runtime.py_set(frame, row_base + x, scene(px, py, light_x, light_y));
                }
            }
            frames.Add(Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_14_raymarching_light_cycle();
    }
}
