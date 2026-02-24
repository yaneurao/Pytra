using math;

public static class Program
{
    // 06: Sample that sweeps Julia-set parameters and outputs a GIF.
    
    public static List<byte> julia_palette()
    {
        // Keep index 0 black for points inside the set; build a high-saturation gradient for the rest.
        List<byte> palette = bytearray(256 * 3);
        palette[System.Convert.ToInt32(0)] = 0;
        palette[System.Convert.ToInt32(1)] = 0;
        palette[System.Convert.ToInt32(2)] = 0;
        for (long i = 1; i < 256; i += 1) {
            double t = (i - 1) / 254.0;
            long r = System.Convert.ToInt64(255.0 * 9.0 * (1.0 - t) * t * t * t);
            long g = System.Convert.ToInt64(255.0 * 15.0 * (1.0 - t) * (1.0 - t) * t * t);
            long b = System.Convert.ToInt64(255.0 * 8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t);
            palette[System.Convert.ToInt32(i * 3 + 0)] = r;
            palette[System.Convert.ToInt32(i * 3 + 1)] = g;
            palette[System.Convert.ToInt32(i * 3 + 2)] = b;
        }
        return bytes(palette);
    }
    
    public static List<byte> render_frame(long width, long height, double cr, double ci, long max_iter, long phase)
    {
        List<byte> frame = bytearray(width * height);
        for (long y = 0; y < height; y += 1) {
            long row_base = y * width;
            double zy0 = -1.2 + 2.4 * (y / (height - 1));
            for (long x = 0; x < width; x += 1) {
                double zx = -1.8 + 3.6 * (x / (width - 1));
                double zy = zy0;
                long i = 0;
                while (i < max_iter) {
                    double zx2 = zx * zx;
                    double zy2 = zy * zy;
                    if (zx2 + zy2 > 4.0) {
                        py_break;
                    }
                    zy = 2.0 * zx * zy + ci;
                    zx = zx2 - zy2 + cr;
                    i += 1;
                }
                if (i >= max_iter) {
                    frame[System.Convert.ToInt32(row_base + x)] = 0;
                } else {
                    // Add a small frame phase so colors flow smoothly.
                    long color_index = 1 + (System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(i * 224) / System.Convert.ToDouble(max_iter))) + phase) % 255;
                    frame[System.Convert.ToInt32(row_base + x)] = color_index;
                }
            }
        }
        return bytes(frame);
    }
    
    public static void run_06_julia_parameter_sweep()
    {
        long width = 320;
        long height = 240;
        long frames_n = 72;
        long max_iter = 180;
        string out_path = "sample/out/06_julia_parameter_sweep.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        // Orbit an ellipse around a known visually good region to reduce flat blown highlights.
        double center_cr = -0.745;
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.10;
        // Add start and phase offsets so GitHub thumbnails do not appear too dark.
        // Tune it to start in a red-leaning color range.
        long start_offset = 20;
        long phase_offset = 180;
        for (long i = 0; i < frames_n; i += 1) {
            double t = (i + start_offset) % frames_n / frames_n;
            unknown angle = 2.0 * math.pi * t;
            unknown cr = center_cr + radius_cr * math.cos(angle);
            unknown ci = center_ci + radius_ci * math.sin(angle);
            long phase = (phase_offset + i * 5) % 255;
            frames.Add(render_frame(width, height, cr, ci, max_iter, phase));
        }
        save_gif(out_path, width, height, frames, julia_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_06_julia_parameter_sweep();
    }
}
