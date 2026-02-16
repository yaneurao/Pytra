using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static int escape_count(double cx, double cy, int max_iter)
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
            if (((x2 + y2) > 4.0))
            {
                return i;
            }
            y = (((2.0 * x) * y) + cy);
            x = ((x2 - y2) + cx);
        }
        return max_iter;
    }

    public static Tuple<int, int, int> color_map(int iter_count, int max_iter)
    {
        if ((iter_count >= max_iter))
        {
            return Tuple.Create(0, 0, 0);
        }
        double t = (iter_count / max_iter);
        int r = (int)((255.0 * (t * t)));
        int g = (int)((255.0 * t));
        int b = (int)((255.0 * (1.0 - t)));
        return Tuple.Create(r, g, b);
    }

    public static List<byte> render_mandelbrot(int width, int height, int max_iter, double x_min, double x_max, double y_min, double y_max)
    {
        List<byte> pixels = new List<byte>();
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = height;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
        {
            double py = (y_min + ((y_max - y_min) * (y / (height - 1))));
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = width;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
            {
                double px = (x_min + ((x_max - x_min) * (x / (width - 1))));
                int it = escape_count(px, py, max_iter);
                int r;
                int g;
                int b;
                if ((it >= max_iter))
                {
                    r = 0;
                    g = 0;
                    b = 0;
                }
                else
                {
                    double t = (it / max_iter);
                    r = (int)((255.0 * (t * t)));
                    g = (int)((255.0 * t));
                    b = (int)((255.0 * (1.0 - t)));
                }
                pixels.Add((byte)(r));
                pixels.Add((byte)(g));
                pixels.Add((byte)(b));
            }
        }
        return pixels;
    }

    public static void run_mandelbrot()
    {
        int width = 800;
        int height = 600;
        int max_iter = 400;
        string out_path = "sample/out/mandelbrot_01.png";
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
