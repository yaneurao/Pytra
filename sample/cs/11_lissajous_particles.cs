using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> color_palette()
    {
        var p = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = i;
            var g = ((i * 3) % 256);
            var b = (255 - i);
            p.Add((byte)(r));
            p.Add((byte)(g));
            p.Add((byte)(b));
        }
        return bytes(p);
    }

    public static void run_11_lissajous_particles()
    {
        var w = 320;
        var h = 240;
        var frames_n = 80;
        var particles = 24;
        var out_path = "sample/out/11_lissajous_particles.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = frames_n;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (t < __pytra_range_stop_5) : (t > __pytra_range_stop_5); t += __pytra_range_step_6)
        {
            var frame = new List<byte>();
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = particles;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var p = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (p < __pytra_range_stop_8) : (p > __pytra_range_stop_8); p += __pytra_range_step_9)
            {
                var phase = (p * 0.261799);
                var x = (int)(((w * 0.5) + ((w * 0.38) * Math.Sin(((0.11 * t) + (phase * 2.0))))));
                var y = (int)(((h * 0.5) + ((h * 0.38) * Math.Sin(((0.17 * t) + (phase * 3.0))))));
                var color = (30 + ((p * 9) % 220));
                var __pytra_range_start_10 = (-2);
                var __pytra_range_stop_11 = 3;
                var __pytra_range_step_12 = 1;
                if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var dy = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dy < __pytra_range_stop_11) : (dy > __pytra_range_stop_11); dy += __pytra_range_step_12)
                {
                    var __pytra_range_start_13 = (-2);
                    var __pytra_range_stop_14 = 3;
                    var __pytra_range_step_15 = 1;
                    if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var dx = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (dx < __pytra_range_stop_14) : (dx > __pytra_range_stop_14); dx += __pytra_range_step_15)
                    {
                        var xx = (x + dx);
                        var yy = (y + dy);
                        if (((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)))
                        {
                            var d2 = ((dx * dx) + (dy * dy));
                            if ((d2 <= 4))
                            {
                                var idx = ((yy * w) + xx);
                                var v = (color - (d2 * 20));
                                if ((v < 0))
                                {
                                    v = 0;
                                }
                                if ((v > frame[idx]))
                                {
                                    // unsupported assignment: frame[idx] = v
                                }
                            }
                        }
                    }
                }
            }
            frames.Add((byte)(bytes(frame)));
        }
        save_gif(out_path, w, h, frames, color_palette(), delay_cs: 3, loop: 0);
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
