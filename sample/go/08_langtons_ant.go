public static class Program
{
    // 08: Sample that outputs Langton's Ant trajectories as a GIF.
    
    public static List<byte> capture(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h)
    {
        List<byte> frame = bytearray(w * h);
        for (long y = 0; y < h; y += 1) {
            long row_base = y * w;
            for (long x = 0; x < w; x += 1) {
                frame[System.Convert.ToInt32(row_base + x)] = (grid[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)] ? 255 : 0);
            }
        }
        return bytes(frame);
    }
    
    public static void run_08_langtons_ant()
    {
        long w = 420;
        long h = 420;
        string out_path = "sample/out/08_langtons_ant.gif";
        
        unknown start = perf_counter();
        
        System.Collections.Generic.List<System.Collections.Generic.List<long>> grid = [[0] * w for _ in range(h)];
        long x = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(w) / System.Convert.ToDouble(2)));
        long y = System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(h) / System.Convert.ToDouble(2)));
        long d = 0;
        
        long steps_total = 600000;
        long capture_every = 3000;
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        for (long i = 0; i < steps_total; i += 1) {
            if (grid[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)] == 0) {
                d = (d + 1) % 4;
                grid[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)] = 1;
            } else {
                d = (d + 3) % 4;
                grid[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)] = 0;
            }
            if (d == 0) {
                y = (y - 1 + h) % h;
            } else {
                if (d == 1) {
                    x = (x + 1) % w;
                } else {
                    if (d == 2) {
                        y = (y + 1) % h;
                    } else {
                        x = (x - 1 + w) % w;
                    }
                }
            }
            if (i % capture_every == 0) {
                frames.Add(capture(grid, w, h));
            }
        }
        save_gif(out_path, w, h, frames, grayscale_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_08_langtons_ant();
    }
}
