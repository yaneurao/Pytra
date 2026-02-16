using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter)
    {
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
        long idx = 0L;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            var zy0 = ((-1.2) + (2.4 * (y / (height - 1L))));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                var zx = ((-1.8) + (3.6 * (x / (width - 1L))));
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
                Pytra.CsModule.py_runtime.py_set(frame, idx, (long)(((255.0 * i) / max_iter)));
                idx = (idx + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_06_julia_parameter_sweep()
    {
        long width = 320L;
        long height = 240L;
        long frames_n = 50L;
        long max_iter = 120L;
        string out_path = "sample/out/06_julia_parameter_sweep.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = frames_n;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (i < __pytra_range_stop_8) : (i > __pytra_range_stop_8); i += __pytra_range_step_9)
        {
            var t = (i / frames_n);
            var cr = ((-0.8) + (0.32 * t));
            var ci = (0.156 + (0.22 * (0.5 - t)));
            Pytra.CsModule.py_runtime.py_append(frames, render_frame(width, height, cr, ci, max_iter));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 4L, loop: 0L);
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
