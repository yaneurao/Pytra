public static class Program
{
    // 09: Sample that outputs a simple fire effect as a GIF.
    
    public static List<byte> fire_palette()
    {
        List<byte> p = bytearray();
        for (long i = 0; i < 256; i += 1) {
            long r = 0;
            long g = 0;
            long b = 0;
            if (i < 85) {
                r = i * 3;
                g = 0;
                b = 0;
            } else {
                if (i < 170) {
                    r = 255;
                    g = (i - 85) * 3;
                    b = 0;
                } else {
                    r = 255;
                    g = 255;
                    b = (i - 170) * 3;
                }
            }
            p.Add(r);
            p.Add(g);
            p.Add(b);
        }
        return bytes(p);
    }
    
    public static void run_09_fire_simulation()
    {
        long w = 380;
        long h = 260;
        long steps = 420;
        string out_path = "sample/out/09_fire_simulation.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<System.Collections.Generic.List<long>> heat = [[0] * w for _ in range(h)];
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        for (long t = 0; t < steps; t += 1) {
            for (long x = 0; x < w; x += 1) {
                long val = 170 + (x * 13 + t * 17) % 86;
                heat[System.Convert.ToInt32(h - 1)][System.Convert.ToInt32(x)] = val;
            }
            for (long y = 1; y < h; y += 1) {
                for (long x = 0; x < w; x += 1) {
                    long a = heat[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)];
                    long b = heat[System.Convert.ToInt32(y)][System.Convert.ToInt32((x - 1 + w) % w)];
                    long c = heat[System.Convert.ToInt32(y)][System.Convert.ToInt32((x + 1) % w)];
                    long d = heat[System.Convert.ToInt32((y + 1) % h)][System.Convert.ToInt32(x)];
                    long v = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble((a + b + c + d)) / System.Convert.ToDouble(4)));
                    long cool = 1 + (x + y + t) % 3;
                    long nv = v - cool;
                    heat[System.Convert.ToInt32(y - 1)][System.Convert.ToInt32(x)] = (nv > 0 ? nv : 0);
                }
            }
            List<byte> frame = bytearray(w * h);
            for (long yy = 0; yy < h; yy += 1) {
                long row_base = yy * w;
                for (long xx = 0; xx < w; xx += 1) {
                    frame[System.Convert.ToInt32(row_base + xx)] = heat[System.Convert.ToInt32(yy)][System.Convert.ToInt32(xx)];
                }
            }
            frames.Add(bytes(frame));
        }
        save_gif(out_path, w, h, frames, fire_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", steps }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_09_fire_simulation();
    }
}
