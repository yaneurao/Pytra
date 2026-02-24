public static class Program
{
    // 03: Sample that outputs a Julia set as a PNG image.
    // Implemented with simple loop-centric logic for transpilation compatibility.
    
    public static List<byte> render_julia(long width, long height, long max_iter, double cx, double cy)
    {
        List<byte> pixels = bytearray();
        for (long y = 0; y < height; y += 1) {
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
                    zy = 2.0 * zx * zy + cy;
                    zx = zx2 - zy2 + cx;
                    i += 1;
                }
                long r = 0;
                long g = 0;
                long b = 0;
                if (i >= max_iter) {
                    r = 0;
                    g = 0;
                    b = 0;
                } else {
                    double t = i / max_iter;
                    r = System.Convert.ToInt64(255.0 * (0.2 + 0.8 * t));
                    g = System.Convert.ToInt64(255.0 * (0.1 + 0.9 * t * t));
                    b = System.Convert.ToInt64(255.0 * (1.0 - t));
                }
                pixels.Add(r);
                pixels.Add(g);
                pixels.Add(b);
            }
        }
        return pixels;
    }
    
    public static void run_julia()
    {
        long width = 3840;
        long height = 2160;
        long max_iter = 20000;
        string out_path = "sample/out/03_julia_set.png";
        
        double start = perf_counter();
        List<byte> pixels = render_julia(width, height, max_iter, -0.8, 0.156);
        png.write_rgb_png(out_path, width, height, pixels);
        double elapsed = perf_counter() - start;
        
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "size:", width, "x", height }));
        System.Console.WriteLine(string.Join(" ", new object[] { "max_iter:", max_iter }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_julia();
    }
}
