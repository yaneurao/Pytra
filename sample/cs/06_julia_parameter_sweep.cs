using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> render_frame(int width, int height, double cr, double ci, int max_iter)
    {
        var frame = new List<byte>();
        var idx = 0;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            var zy0 = ((-1.2) + (2.4 * (y / (height - 1))));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                var zx = ((-1.8) + (3.6 * (x / (width - 1))));
                var zy = zy0;
                var i = 0;
                while ((i < max_iter))
                {
                    var zx2 = (zx * zx);
                    var zy2 = (zy * zy);
                    if (((zx2 + zy2) > 4.0))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + ci);
                    zx = ((zx2 - zy2) + cr);
                    i = (i + 1);
                }
                // unsupported assignment: frame[idx] = int(255.0 * i / max_iter)
                idx = (idx + 1);
            }
        }
        return bytes(frame);
    }

    public static void run_06_julia_parameter_sweep()
    {
        var width = 320;
        var height = 240;
        var frames_n = 50;
        var max_iter = 120;
        var out_path = "sample/out/06_julia_parameter_sweep.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = frames_n;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (i < __pytra_range_stop_8) : (i > __pytra_range_stop_8); i += __pytra_range_step_9)
        {
            var t = (i / frames_n);
            var cr = ((-0.8) + (0.32 * t));
            var ci = (0.156 + (0.22 * (0.5 - t)));
            frames.Add((byte)(render_frame(width, height, cr, ci, max_iter)));
        }
        save_gif(out_path, width, height, frames, grayscale_palette(), delay_cs: 4, loop: 0);
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
