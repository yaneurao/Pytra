using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using math = Pytra.CsModule.math;

public static class Program
{
    // 06: Sample that sweeps Julia-set parameters and outputs a GIF.
    
    public static List<byte> julia_palette()
    {
        // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
        List<byte> palette = Pytra.CsModule.py_runtime.py_bytearray(256 * 3);
        Pytra.CsModule.py_runtime.py_set(palette, 0, 0);
        Pytra.CsModule.py_runtime.py_set(palette, 1, 0);
        Pytra.CsModule.py_runtime.py_set(palette, 2, 0);
        long i = 1;
        for (i = 1; i < 256; i += 1) {
            double t = (i - 1) / 254.0;
            long r = Pytra.CsModule.py_runtime.py_int(255.0 * 9.0 * (1.0 - t) * t * t * t);
            long g = Pytra.CsModule.py_runtime.py_int(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t);
            long b = Pytra.CsModule.py_runtime.py_int(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t);
            Pytra.CsModule.py_runtime.py_set(palette, i * 3 + 0, r);
            Pytra.CsModule.py_runtime.py_set(palette, i * 3 + 1, g);
            Pytra.CsModule.py_runtime.py_set(palette, i * 3 + 2, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(palette);
    }
    
    public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter, long phase)
    {
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(width * height);
        double __hoisted_cast_1 = System.Convert.ToDouble(height - 1);
        double __hoisted_cast_2 = System.Convert.ToDouble(width - 1);
        long y = 0;
        for (y = 0; y < height; y += 1) {
            long row_base = y * width;
            double zy0 = -1.2 + 2.4 * (y / __hoisted_cast_1);
            long x = 0;
            for (x = 0; x < width; x += 1) {
                double zx = -1.8 + 3.6 * (x / __hoisted_cast_2);
                double zy = zy0;
                long i = 0;
                while (i < max_iter) {
                    double zx2 = zx * zx;
                    double zy2 = zy * zy;
                    if (zx2 + zy2 > 4.0) {
                        break;
                    }
                    zy = 2.0 * zx * zy + ci;
                    zx = zx2 - zy2 + cr;
                    i += 1;
                }
                if (i >= max_iter) {
                    Pytra.CsModule.py_runtime.py_set(frame, row_base + x, 0);
                } else {
                    // Add a small frame phase so colors flow smoothly.
                    long color_index = 1 + (System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(i * 224) / System.Convert.ToDouble(max_iter))) + phase) % 255;
                    Pytra.CsModule.py_runtime.py_set(frame, row_base + x, color_index);
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_06_julia_parameter_sweep()
    {
        long width = 320;
        long height = 240;
        long frames_n = 72;
        long max_iter = 180;
        string out_path = "sample/out/06_julia_parameter_sweep.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
        double center_cr = -0.745;
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.10;
        // Add start and phase offsets so GitHub thumbnails do not appear too dark.
        // Tune it to start in a red-leaning color range.
        long start_offset = 20;
        long phase_offset = 180;
        double __hoisted_cast_3 = System.Convert.ToDouble(frames_n);
        long i = 0;
        for (i = 0; i < frames_n; i += 1) {
            double t = (i + start_offset) % frames_n / __hoisted_cast_3;
            var angle = 2.0 * Pytra.CsModule.math.pi * t;
            var cr = center_cr + radius_cr * Pytra.CsModule.math.cos(angle);
            var ci = center_ci + radius_ci * Pytra.CsModule.math.sin(angle);
            long phase = (phase_offset + i * 5) % 255;
            frames.Add(render_frame(width, height, cr, ci, max_iter, phase));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, julia_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_06_julia_parameter_sweep();
    }
}
