using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 09: Sample that outputs a simple fire effect as a GIF.
    
    public static List<byte> fire_palette()
    {
        List<byte> p = new System.Collections.Generic.List<byte>();
        long i = 0;
        for (i = 0; i < 256; i += 1) {
            long r = 0;
            long g = 0;
            long b = 0;
            if (i < 85) {
                r = i * 3;
                g = 0;
                b = 0;
            } else {
                if (i < 170) {
                    r = 255;
                    g = (i - 85) * 3;
                    b = 0;
                } else {
                    r = 255;
                    g = 255;
                    b = (i - 170) * 3;
                }
            }
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }
    
    public static void run_09_fire_simulation()
    {
        long w = 380;
        long h = 260;
        long steps = 420;
        string out_path = "sample/out/09_fire_simulation.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<System.Collections.Generic.List<long>> heat = (new System.Func<System.Collections.Generic.List<System.Collections.Generic.List<long>>>(() => { var __out_5 = new System.Collections.Generic.List<System.Collections.Generic.List<long>>(); foreach (var __it_6 in (new System.Func<System.Collections.Generic.List<long>>(() => { var __out_7 = new System.Collections.Generic.List<long>(); long __start_8 = System.Convert.ToInt64(0); long __stop_9 = System.Convert.ToInt64(h); long __step_10 = System.Convert.ToInt64(1); if (__step_10 == 0) { return __out_7; } if (__step_10 > 0) { for (long __i_11 = __start_8; __i_11 < __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } else { for (long __i_11 = __start_8; __i_11 > __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } return __out_7; }))()) { __out_5.Add((new System.Func<System.Collections.Generic.List<long>>(() => { var __base_1 = new System.Collections.Generic.List<long> { 0 }; long __n_2 = System.Convert.ToInt64(w); if (__n_2 < 0) { __n_2 = 0; } var __out_3 = new System.Collections.Generic.List<long>(); for (long __i_4 = 0; __i_4 < __n_2; __i_4 += 1) { __out_3.AddRange(__base_1); } return __out_3; }))()); } return __out_5; }))();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        
        long t = 0;
        for (t = 0; t < steps; t += 1) {
            long x = 0;
            for (x = 0; x < w; x += 1) {
                long val = 170 + (x * 13 + t * 17) % 86;
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(heat, h - 1), x, val);
            }
            long y = 1;
            for (y = 1; y < h; y += 1) {
                for (x = 0; x < w; x += 1) {
                    long a = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), x);
                    long b = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), (x - 1 + w) % w);
                    long c = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), (x + 1) % w);
                    long d = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, (y + 1) % h), x);
                    long v = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble((a + b + c + d)) / System.Convert.ToDouble(4)));
                    long cool = 1 + (x + y + t) % 3;
                    long nv = v - cool;
                    Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(heat, y - 1), x, (nv > 0 ? nv : 0));
                }
            }
            List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
            long yy = 0;
            for (yy = 0; yy < h; yy += 1) {
                long row_base = yy * w;
                long xx = 0;
                for (xx = 0; xx < w; xx += 1) {
                    Pytra.CsModule.py_runtime.py_set(frame, row_base + xx, Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, yy), xx));
                }
            }
            frames.Add(Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, fire_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", steps }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_09_fire_simulation();
    }
}
