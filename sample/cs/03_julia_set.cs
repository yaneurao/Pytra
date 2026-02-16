using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> render_julia(long width, long height, long max_iter, double cx, double cy)
    {
        List<byte> pixels = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = height;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            double zy0 = ((-1.2) + (2.4 * ((double)(y) / (double)((height - 1L)))));
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = width;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                double zx = ((-1.8) + (3.6 * ((double)(x) / (double)((width - 1L)))));
                double zy = zy0;
                long i = 0L;
                while (Pytra.CsModule.py_runtime.py_bool((i < max_iter)))
                {
                    double zx2 = (zx * zx);
                    double zy2 = (zy * zy);
                    if (Pytra.CsModule.py_runtime.py_bool(((zx2 + zy2) > 4.0)))
                    {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + cy);
                    zx = ((zx2 - zy2) + cx);
                    i = (i + 1L);
                }
                long r = 0L;
                long g = 0L;
                long b = 0L;
                if (Pytra.CsModule.py_runtime.py_bool((i >= max_iter)))
                {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                }
                else
                {
                    double t = ((double)(i) / (double)(max_iter));
                    r = (long)((255.0 * (0.2 + (0.8 * t))));
                    g = (long)((255.0 * (0.1 + (0.9 * (t * t)))));
                    b = (long)((255.0 * (1.0 - t)));
                }
                Pytra.CsModule.py_runtime.py_append(pixels, r);
                Pytra.CsModule.py_runtime.py_append(pixels, g);
                Pytra.CsModule.py_runtime.py_append(pixels, b);
            }
        }
        return pixels;
    }

    public static void run_julia()
    {
        long width = 3840L;
        long height = 2160L;
        long max_iter = 20000L;
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
