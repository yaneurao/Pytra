using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> palette()
    {
        var p = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = (long)((20L + (i * 0.9)));
            if (Pytra.CsModule.py_runtime.py_bool((r > 255L)))
            {
                r = 255L;
            }
            var g = (long)((10L + (i * 0.7)));
            if (Pytra.CsModule.py_runtime.py_bool((g > 255L)))
            {
                g = 255L;
            }
            var b = (long)((30L + i));
            if (Pytra.CsModule.py_runtime.py_bool((b > 255L)))
            {
                b = 255L;
            }
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }

    public static long scene(double x, double y, double light_x, double light_y)
    {
        var x1 = (x + 0.45);
        var y1 = (y + 0.2);
        var x2 = (x - 0.35);
        var y2 = (y - 0.15);
        var r1 = Math.Sqrt(((x1 * x1) + (y1 * y1)));
        var r2 = Math.Sqrt(((x2 * x2) + (y2 * y2)));
        var blob = (Math.Exp((((-7.0) * r1) * r1)) + Math.Exp((((-8.0) * r2) * r2)));
        var lx = (x - light_x);
        var ly = (y - light_y);
        var l = Math.Sqrt(((lx * lx) + (ly * ly)));
        var lit = ((double)(1.0) / (double)((1.0 + ((3.5 * l) * l))));
        var v = (long)((((255.0 * blob) * lit) * 5.0));
        if (Pytra.CsModule.py_runtime.py_bool((v < 0L)))
        {
            return 0L;
        }
        if (Pytra.CsModule.py_runtime.py_bool((v > 255L)))
        {
            return 255L;
        }
        return v;
    }

    public static void run_14_raymarching_light_cycle()
    {
        long w = 320L;
        long h = 240L;
        long frames_n = 84L;
        string out_path = "sample/out/14_raymarching_light_cycle.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = frames_n;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (t < __pytra_range_stop_5) : (t > __pytra_range_stop_5); t += __pytra_range_step_6)
        {
            var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
            var a = ((((double)(t) / (double)(frames_n)) * Math.PI) * 2.0);
            var light_x = (0.75 * Math.Cos(a));
            var light_y = (0.55 * Math.Sin((a * 1.2)));
            long i = 0L;
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = h;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var y = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (y < __pytra_range_stop_8) : (y > __pytra_range_stop_8); y += __pytra_range_step_9)
            {
                var py = ((((double)(y) / (double)((h - 1L))) * 2.0) - 1.0);
                var __pytra_range_start_10 = 0;
                var __pytra_range_stop_11 = w;
                var __pytra_range_step_12 = 1;
                if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var x = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (x < __pytra_range_stop_11) : (x > __pytra_range_stop_11); x += __pytra_range_step_12)
                {
                    var px = ((((double)(x) / (double)((w - 1L))) * 2.0) - 1.0);
                    Pytra.CsModule.py_runtime.py_set(frame, i, scene(px, py, light_x, light_y));
                    i = (i + 1L);
                }
            }
            Pytra.CsModule.py_runtime.py_append(frames, Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, palette(), delay_cs: 3L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_14_raymarching_light_cycle();
    }
}
