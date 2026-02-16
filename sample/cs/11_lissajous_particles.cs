using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> color_palette()
    {
        var p = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = i;
            var g = ((i * 3L) % 256L);
            var b = (255L - i);
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }

    public static void run_11_lissajous_particles()
    {
        long w = 320L;
        long h = 240L;
        long frames_n = 80L;
        long particles = 24L;
        string out_path = "sample/out/11_lissajous_particles.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = frames_n;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (t < __pytra_range_stop_5) : (t > __pytra_range_stop_5); t += __pytra_range_step_6)
        {
            var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = particles;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var p = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (p < __pytra_range_stop_8) : (p > __pytra_range_stop_8); p += __pytra_range_step_9)
            {
                var phase = (p * 0.261799);
                var x = (long)(((w * 0.5) + ((w * 0.38) * Math.Sin(((0.11 * t) + (phase * 2.0))))));
                var y = (long)(((h * 0.5) + ((h * 0.38) * Math.Sin(((0.17 * t) + (phase * 3.0))))));
                var color = (30L + ((p * 9L) % 220L));
                var __pytra_range_start_10 = (-2L);
                var __pytra_range_stop_11 = 3L;
                var __pytra_range_step_12 = 1;
                if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var dy = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dy < __pytra_range_stop_11) : (dy > __pytra_range_stop_11); dy += __pytra_range_step_12)
                {
                    var __pytra_range_start_13 = (-2L);
                    var __pytra_range_stop_14 = 3L;
                    var __pytra_range_step_15 = 1;
                    if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var dx = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (dx < __pytra_range_stop_14) : (dx > __pytra_range_stop_14); dx += __pytra_range_step_15)
                    {
                        var xx = (x + dx);
                        var yy = (y + dy);
                        if (Pytra.CsModule.py_runtime.py_bool(((xx >= 0L) && (xx < w) && (yy >= 0L) && (yy < h))))
                        {
                            var d2 = ((dx * dx) + (dy * dy));
                            if (Pytra.CsModule.py_runtime.py_bool((d2 <= 4L)))
                            {
                                var idx = ((yy * w) + xx);
                                var v = (color - (d2 * 20L));
                                if (Pytra.CsModule.py_runtime.py_bool((v < 0L)))
                                {
                                    v = 0L;
                                }
                                if (Pytra.CsModule.py_runtime.py_bool((v > Pytra.CsModule.py_runtime.py_get(frame, idx))))
                                {
                                    Pytra.CsModule.py_runtime.py_set(frame, idx, v);
                                }
                            }
                        }
                    }
                }
            }
            Pytra.CsModule.py_runtime.py_append(frames, Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, color_palette(), delay_cs: 3L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_11_lissajous_particles();
    }
}
