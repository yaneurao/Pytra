using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 05: Sample that outputs a Mandelbrot zoom as an animated GIF.
    
    public static List<byte> render_frame(long width, long height, double center_x, double center_y, double scale, long max_iter)
    {
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(width * height);
        double __hoisted_cast_1 = System.Convert.ToDouble(max_iter);
        long y = 0;
        for (y = 0; y < height; y += 1) {
            long row_base = y * width;
            double cy = center_y + (y - height * 0.5) * scale;
            long x = 0;
            for (x = 0; x < width; x += 1) {
                double cx = center_x + (x - width * 0.5) * scale;
                double zx = 0.0;
                double zy = 0.0;
                long i = 0;
                while (i < max_iter) {
                    double zx2 = zx * zx;
                    double zy2 = zy * zy;
                    if (zx2 + zy2 > 4.0) {
                        break;
                    }
                    zy = 2.0 * zx * zy + cy;
                    zx = zx2 - zy2 + cx;
                    i += 1;
                }
                Pytra.CsModule.py_runtime.py_set(frame, row_base + x, Pytra.CsModule.py_runtime.py_int(255.0 * i / __hoisted_cast_1));
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_05_mandelbrot_zoom()
    {
        long width = 320;
        long height = 240;
        long frame_count = 48;
        long max_iter = 110;
        double center_x = -0.743643887037151;
        double center_y = 0.13182590420533;
        double base_scale = 3.2 / width;
        double zoom_per_frame = 0.93;
        string out_path = "sample/out/05_mandelbrot_zoom.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        double scale = base_scale;
        long _ = 0;
        for (_ = 0; _ < frame_count; _ += 1) {
            frames.Add(render_frame(width, height, center_x, center_y, scale, max_iter));
            scale *= zoom_per_frame;
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, width, height, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frame_count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_05_mandelbrot_zoom();
    }
}
