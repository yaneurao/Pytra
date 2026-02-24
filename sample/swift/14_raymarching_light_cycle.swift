using math;

public static class Program
{
    // 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.
    
    public static List<byte> palette()
    {
        List<byte> p = bytearray();
        for (long i = 0; i < 256; i += 1) {
            unknown r = min(255, System.Convert.ToInt64(20 + i * 0.9));
            unknown g = min(255, System.Convert.ToInt64(10 + i * 0.7));
            unknown b = min(255, System.Convert.ToInt64(30 + i));
            p.Add(r);
            p.Add(g);
            p.Add(b);
        }
        return bytes(p);
    }
    
    public static long scene(double x, double y, double light_x, double light_y)
    {
        double x1 = x + 0.45;
        double y1 = y + 0.2;
        double x2 = x - 0.35;
        double y2 = y - 0.15;
        unknown r1 = math.sqrt(x1 * x1 + y1 * y1);
        unknown r2 = math.sqrt(x2 * x2 + y2 * y2);
        unknown blob = math.exp(-7.0 * r1 * r1) + math.exp(-8.0 * r2 * r2);
        
        double lx = x - light_x;
        double ly = y - light_y;
        unknown l = math.sqrt(lx * lx + ly * ly);
        unknown lit = 1.0 / (1.0 + 3.5 * l * l);
        
        long v = System.Convert.ToInt64(255.0 * blob * lit * 5.0);
        return min(255, max(0, v));
    }
    
    public static void run_14_raymarching_light_cycle()
    {
        long w = 320;
        long h = 240;
        long frames_n = 84;
        string out_path = "sample/out/14_raymarching_light_cycle.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        for (long t = 0; t < frames_n; t += 1) {
            List<byte> frame = bytearray(w * h);
            unknown a = (t / frames_n) * math.pi * 2.0;
            unknown light_x = 0.75 * math.cos(a);
            unknown light_y = 0.55 * math.sin(a * 1.2);
            for (long y = 0; y < h; y += 1) {
                long row_base = y * w;
                double py = (y / (h - 1)) * 2.0 - 1.0;
                for (long x = 0; x < w; x += 1) {
                    double px = (x / (w - 1)) * 2.0 - 1.0;
                    frame[System.Convert.ToInt32(row_base + x)] = scene(px, py, light_x, light_y);
                }
            }
            frames.Add(bytes(frame));
        }
        save_gif(out_path, w, h, frames, palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_14_raymarching_light_cycle();
    }
}
