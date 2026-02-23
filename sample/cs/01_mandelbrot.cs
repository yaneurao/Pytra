using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static long escape_count(double cx, double cy, long max_iter)
    {
        double x = 0.0;
        double y = 0.0;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = max_iter;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            double x2 = (x * x);
            double y2 = (y * y);
            if (Pytra.CsModule.py_runtime.py_bool(((x2 + y2) > 4.0)))
            {
                return i;
            }
            y = (((2.0 * x) * y) + cy);
            x = ((x2 - y2) + cx);
        }
        return max_iter;
    }

    public static Tuple<long, long, long> color_map(long iter_count, long max_iter)
    {
        if (Pytra.CsModule.py_runtime.py_bool((iter_count >= max_iter)))
        {
            return Tuple.Create(0L, 0L, 0L);
        }
        double t = ((double)(iter_count) / (double)(max_iter));
        long r = (long)((255.0 * (t * t)));
        long g = (long)((255.0 * t));
        long b = (long)((255.0 * (1.0 - t)));
        return Tuple.Create(r, g, b);
    }

    public static List<byte> render_mandelbrot(long width, long height, long max_iter, double x_min, double x_max, double y_min, double y_max)
    {
        List<byte> pixels = new List<byte>();
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = height;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            double py = (y_min + ((y_max - y_min) * ((double)(y) / (double)((height - 1L)))));
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = width;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                double px = (x_min + ((x_max - x_min) * ((double)(x) / (double)((width - 1L)))));
                long it = escape_count(px, py, max_iter);
                long r;
                long g;
                long b;
                if (Pytra.CsModule.py_runtime.py_bool((it >= max_iter)))
                {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                }
                else
                {
                    double t = ((double)(it) / (double)(max_iter));
                    r = (long)((255.0 * (t * t)));
                    g = (long)((255.0 * t));
                    b = (long)((255.0 * (1.0 - t)));
                }
                Pytra.CsModule.py_runtime.py_append(pixels, r);
                Pytra.CsModule.py_runtime.py_append(pixels, g);
                Pytra.CsModule.py_runtime.py_append(pixels, b);
            }
        }
        return pixels;
    }

    public static void run_mandelbrot()
    {
        long width = 1600L;
        long height = 1200L;
        long max_iter = 1000L;
        string out_path = "sample/out/01_mandelbrot.png";
        double start = Pytra.CsModule.time.perf_counter();
        List<byte> pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2);
        Pytra.CsModule.png_helper.write_rgb_png(out_path, width, height, pixels);
        double elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("size:", width, "x", height);
        Pytra.CsModule.py_runtime.print("max_iter:", max_iter);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_mandelbrot();
    }
}
