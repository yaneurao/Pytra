using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> render_julia(int width, int height, int max_iter, double cx, double cy)
    {
        List<byte> pixels = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            double zy0 = ((-1.2) + (2.4 * (y / (height - 1))));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                double zx = ((-1.8) + (3.6 * (x / (width - 1))));
                double zy = zy0;
                int i = 0;
                while ((i < max_iter))
                {
                    double zx2 = (zx * zx);
                    double zy2 = (zy * zy);
                    if (((zx2 + zy2) > 4.0))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + cy);
                    zx = ((zx2 - zy2) + cx);
                    i = (i + 1);
                }
                int r = 0;
                int g = 0;
                int b = 0;
                if ((i >= max_iter))
                {
                    r = 0;
                    g = 0;
                    b = 0;
                }
                else
                {
                    double t = (i / max_iter);
                    r = (int)((255.0 * (0.2 + (0.8 * t))));
                    g = (int)((255.0 * (0.1 + (0.9 * (t * t)))));
                    b = (int)((255.0 * (1.0 - t)));
                }
                pixels.Add((byte)(r));
                pixels.Add((byte)(g));
                pixels.Add((byte)(b));
            }
        }
        return pixels;
    }

    public static void run_julia()
    {
        int width = 1280;
        int height = 720;
        int max_iter = 520;
        string out_path = "sample/out/julia_03.png";
        double start = Pytra.CsModule.time.perf_counter();
        List<byte> pixels = render_julia(width, height, max_iter, (-0.8), 0.156);
        Pytra.CsModule.png_helper.write_rgb_png(out_path, width, height, pixels);
        double elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("size:", width, "x", height);
        Pytra.CsModule.py_runtime.print("max_iter:", max_iter);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_julia();
    }
}
