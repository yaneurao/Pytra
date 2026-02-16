using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static void run_10_plasma_effect()
    {
        long w = 320L;
        long h = 240L;
        long frames_n = 216L;
        string out_path = "sample/out/10_plasma_effect.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = frames_n;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (t < __pytra_range_stop_2) : (t > __pytra_range_stop_2); t += __pytra_range_step_3)
        {
            var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
            long i = 0L;
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = h;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
            {
                var __pytra_range_start_7 = 0;
                var __pytra_range_stop_8 = w;
                var __pytra_range_step_9 = 1;
                if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
                {
                    var dx = (x - 160L);
                    var dy = (y - 120L);
                    var v = (((Math.Sin(((x + (t * 2.0)) * 0.045)) + Math.Sin(((y - (t * 1.2)) * 0.05))) + Math.Sin((((x + y) + (t * 1.7)) * 0.03))) + Math.Sin(((Math.Sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))));
                    var c = (long)(((v + 4.0) * ((double)(255.0) / (double)(8.0))));
                    if (Pytra.CsModule.py_runtime.py_bool((c < 0L)))
                    {
                        c = 0L;
                    }
                    if (Pytra.CsModule.py_runtime.py_bool((c > 255L)))
                    {
                        c = 255L;
                    }
                    Pytra.CsModule.py_runtime.py_set(frame, i, c);
                    i = (i + 1L);
                }
            }
            Pytra.CsModule.py_runtime.py_append(frames, Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 3L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_10_plasma_effect();
    }
}
