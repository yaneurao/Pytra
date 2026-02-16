using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> render_frame(int width, int height, double center_x, double center_y, double scale, int max_iter)
    {
        var frame = new List<byte>();
        var idx = 0;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            var cy = (center_y + ((y - (height * 0.5)) * scale));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                var cx = (center_x + ((x - (width * 0.5)) * scale));
                var zx = 0.0;
                var zy = 0.0;
                var i = 0;
                while ((i < max_iter))
                {
                    var zx2 = (zx * zx);
                    var zy2 = (zy * zy);
                    if (((zx2 + zy2) > 4.0))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + cy);
                    zx = ((zx2 - zy2) + cx);
                    i = (i + 1);
                }
                // unsupported assignment: frame[idx] = int(255.0 * i / max_iter)
                idx = (idx + 1);
            }
        }
        return bytes(frame);
    }

    public static void run_05_mandelbrot_zoom()
    {
        var width = 320;
        var height = 240;
        var frame_count = 48;
        var max_iter = 110;
        var center_x = (-0.743643887037151);
        var center_y = 0.13182590420533;
        var base_scale = (3.2 / width);
        var zoom_per_frame = 0.93;
        var out_path = "sample/out/05_mandelbrot_zoom.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<byte>> frames = new List<object> {  };
        var scale = base_scale;
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = frame_count;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var _ = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (_ < __pytra_range_stop_8) : (_ > __pytra_range_stop_8); _ += __pytra_range_step_9)
        {
            frames.Add((byte)(render_frame(width, height, center_x, center_y, scale, max_iter)));
            scale = (scale * zoom_per_frame);
        }
        save_gif(out_path, width, height, frames, grayscale_palette(), delay_cs: 5, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", frame_count);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_05_mandelbrot_zoom();
    }
}
