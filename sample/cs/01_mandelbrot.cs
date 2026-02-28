using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using png = Pytra.CsModule.png_helper;

public static class Program
{
    // 01: Sample that outputs the Mandelbrot set as a PNG image.
    // Syntax is kept straightforward with future transpilation in mind.
    
    public static long escape_count(double cx, double cy, long max_iter)
    {
        double x = 0.0;
        double y = 0.0;
        long i = 0;
        for (i = 0; i < max_iter; i += 1) {
            double x2 = x * x;
            double y2 = y * y;
            if (x2 + y2 > 4.0) {
                return i;
            }
            y = 2.0 * x * y + cy;
            x = x2 - y2 + cx;
        }
        return max_iter;
    }
    
    public static (long, long, long) color_map(long iter_count, long max_iter)
    {
        if (iter_count >= max_iter) {
            return (0, 0, 0);
        }
        double t = iter_count / max_iter;
        long r = Pytra.CsModule.py_runtime.py_int(255.0 * t * t);
        long g = Pytra.CsModule.py_runtime.py_int(255.0 * t);
        long b = Pytra.CsModule.py_runtime.py_int(255.0 * (1.0 - t));
        return (r, g, b);
    }
    
    public static List<byte> render_mandelbrot(long width, long height, long max_iter, double x_min, double x_max, double y_min, double y_max)
    {
        List<byte> pixels = new System.Collections.Generic.List<byte>();
        double __hoisted_cast_1 = System.Convert.ToDouble(height - 1);
        double __hoisted_cast_2 = System.Convert.ToDouble(width - 1);
        double __hoisted_cast_3 = System.Convert.ToDouble(max_iter);
        
        long y = 0;
        for (y = 0; y < height; y += 1) {
            double py = y_min + (y_max - y_min) * (y / __hoisted_cast_1);
            
            long x = 0;
            for (x = 0; x < width; x += 1) {
                double px = x_min + (x_max - x_min) * (x / __hoisted_cast_2);
                long it = escape_count(px, py, max_iter);
                long r;
                long g;
                long b;
                if (it >= max_iter) {
                    r = 0;
                    g = 0;
                    b = 0;
                } else {
                    double t = it / __hoisted_cast_3;
                    r = Pytra.CsModule.py_runtime.py_int(255.0 * t * t);
                    g = Pytra.CsModule.py_runtime.py_int(255.0 * t);
                    b = Pytra.CsModule.py_runtime.py_int(255.0 * (1.0 - t));
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
        long width = 1600;
        long height = 1200;
        long max_iter = 1000;
        string out_path = "sample/out/01_mandelbrot.png";
        
        double start = Pytra.CsModule.time.perf_counter();
        
        List<byte> pixels = render_mandelbrot(width, height, max_iter, -2.2, 1.0, -1.2, 1.2);
        Pytra.CsModule.png_helper.write_rgb_png(out_path, width, height, pixels);
        
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "size:", width, "x", height }));
        System.Console.WriteLine(string.Join(" ", new object[] { "max_iter:", max_iter }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_mandelbrot();
    }
}
