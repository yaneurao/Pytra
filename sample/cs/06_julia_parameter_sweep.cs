using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> julia_palette()
    {
        var palette = Pytra.CsModule.py_runtime.py_bytearray((256L * 3L));
        Pytra.CsModule.py_runtime.py_set(palette, 0L, 0L);
        Pytra.CsModule.py_runtime.py_set(palette, 1L, 0L);
        Pytra.CsModule.py_runtime.py_set(palette, 2L, 0L);
        var __pytra_range_start_1 = 1L;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var t = ((double)((i - 1L)) / (double)(254.0));
            var r = (long)((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)));
            var g = (long)((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)));
            var b = (long)((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)));
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 0L), r);
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 1L), g);
            Pytra.CsModule.py_runtime.py_set(palette, ((i * 3L) + 2L), b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(palette);
    }

    public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter, long phase)
    {
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
        long idx = 0L;
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = height;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            var zy0 = ((-1.2) + (2.4 * ((double)(y) / (double)((height - 1L)))));
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = width;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                var zx = ((-1.8) + (3.6 * ((double)(x) / (double)((width - 1L)))));
                var zy = zy0;
                long i = 0L;
                while (Pytra.CsModule.py_runtime.py_bool((i < max_iter)))
                {
                    var zx2 = (zx * zx);
                    var zy2 = (zy * zy);
                    if (Pytra.CsModule.py_runtime.py_bool(((zx2 + zy2) > 4.0)))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + ci);
                    zx = ((zx2 - zy2) + cr);
                    i = (i + 1L);
                }
                if (Pytra.CsModule.py_runtime.py_bool((i >= max_iter)))
                {
                    Pytra.CsModule.py_runtime.py_set(frame, idx, 0L);
                }
                else
                {
                    var color_index = (1L + (((long)Math.Floor(((i * 224L)) / (double)(max_iter)) + phase) % 255L));
                    Pytra.CsModule.py_runtime.py_set(frame, idx, color_index);
                }
                idx = (idx + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_06_julia_parameter_sweep()
    {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        long max_iter = 180L;
        string out_path = "sample/out/06_julia_parameter_sweep.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var center_cr = (-0.745);
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.1;
        long start_offset = 20L;
        long phase_offset = 180L;
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = frames_n;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
        {
            var t = ((double)(((i + start_offset) % frames_n)) / (double)(frames_n));
            var angle = ((2.0 * Math.PI) * t);
            var cr = (center_cr + (radius_cr * Math.Cos(angle)));
            var ci = (center_ci + (radius_ci * Math.Sin(angle)));
            var phase = ((phase_offset + (i * 5L)) % 255L);
            Pytra.CsModule.py_runtime.py_append(frames, render_frame(width, height, cr, ci, max_iter, phase));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, julia_palette(), delay_cs: 8L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frames_n);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_06_julia_parameter_sweep();
    }
}
