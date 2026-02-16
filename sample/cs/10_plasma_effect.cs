using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static void run_10_plasma_effect()
    {
        var w = 320;
        var h = 240;
        var frames_n = 72;
        var out_path = "sample/out/10_plasma_effect.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = frames_n;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (t < __pytra_range_stop_2) : (t > __pytra_range_stop_2); t += __pytra_range_step_3)
        {
            var frame = new List<byte>();
            var i = 0;
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
                    var dx = (x - 160);
                    var dy = (y - 120);
                    var v = (((Math.Sin(((x + (t * 2.0)) * 0.045)) + Math.Sin(((y - (t * 1.2)) * 0.05))) + Math.Sin((((x + y) + (t * 1.7)) * 0.03))) + Math.Sin(((Math.Sqrt(((dx * dx) + (dy * dy))) * 0.07) - (t * 0.18))));
                    var c = (int)(((v + 4.0) * (255.0 / 8.0)));
                    if ((c < 0))
                    {
                        c = 0;
                    }
                    if ((c > 255))
                    {
                        c = 255;
                    }
                    // unsupported assignment: frame[i] = c
                    i = (i + 1);
                }
            }
            frames.Add((byte)(bytes(frame)));
        }
        save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs: 3, loop: 0);
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
