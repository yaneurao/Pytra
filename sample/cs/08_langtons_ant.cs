using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 08: Sample that outputs Langton's Ant trajectories as a GIF.
    
    public static List<byte> capture(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h)
    {
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
        long y = 0;
        for (y = 0; y < h; y += 1) {
            long row_base = y * w;
            long x = 0;
            for (x = 0; x < w; x += 1) {
                Pytra.CsModule.py_runtime.py_set(frame, row_base + x, (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) != 0 ? 255 : 0));
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_08_langtons_ant()
    {
        long w = 420;
        long h = 420;
        string out_path = "sample/out/08_langtons_ant.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        
        System.Collections.Generic.List<System.Collections.Generic.List<long>> grid = (new System.Func<System.Collections.Generic.List<System.Collections.Generic.List<long>>>(() => { var __out_5 = new System.Collections.Generic.List<System.Collections.Generic.List<long>>(); foreach (var __it_6 in (new System.Func<System.Collections.Generic.List<long>>(() => { var __out_7 = new System.Collections.Generic.List<long>(); long __start_8 = System.Convert.ToInt64(0); long __stop_9 = System.Convert.ToInt64(h); long __step_10 = System.Convert.ToInt64(1); if (__step_10 == 0) { return __out_7; } if (__step_10 > 0) { for (long __i_11 = __start_8; __i_11 < __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } else { for (long __i_11 = __start_8; __i_11 > __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } return __out_7; }))()) { __out_5.Add((new System.Func<System.Collections.Generic.List<long>>(() => { var __base_1 = new System.Collections.Generic.List<long> { 0 }; long __n_2 = System.Convert.ToInt64(w); if (__n_2 < 0) { __n_2 = 0; } var __out_3 = new System.Collections.Generic.List<long>(); for (long __i_4 = 0; __i_4 < __n_2; __i_4 += 1) { __out_3.AddRange(__base_1); } return __out_3; }))()); } return __out_5; }))();
        long x = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(w) / System.Convert.ToDouble(2)));
        long y = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(h) / System.Convert.ToDouble(2)));
        long d = 0;
        
        long steps_total = 600000;
        long capture_every = 3000;
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        
        long i = 0;
        for (i = 0; i < steps_total; i += 1) {
            if (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) == 0) {
                d = (d + 1) % 4;
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, y), x, 1);
            } else {
                d = (d + 3) % 4;
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, y), x, 0);
            }
            if (d == 0) {
                y = (y - 1 + h) % h;
            } else {
                if (d == 1) {
                    x = (x + 1) % w;
                } else {
                    if (d == 2) {
                        y = (y + 1) % h;
                    } else {
                        x = (x - 1 + w) % w;
                    }
                }
            }
            if (i % capture_every == 0) {
                frames.Add(capture(grid, w, h));
            }
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_08_langtons_ant();
    }
}
