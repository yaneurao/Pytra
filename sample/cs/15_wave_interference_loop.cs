using math;

public static class Program
{
    // 15: Sample that renders wave interference animation and writes a GIF.
    
    public static void run_15_wave_interference_loop()
    {
        long w = 320;
        long h = 240;
        long frames_n = 96;
        string out_path = "sample/out/15_wave_interference_loop.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        
        for (long t = 0; t < frames_n; t += 1) {
            List<byte> frame = bytearray(w * h);
            double phase = t * 0.12;
            for (long y = 0; y < h; y += 1) {
                long row_base = y * w;
                for (long x = 0; x < w; x += 1) {
                    long dx = x - 160;
                    long dy = y - 120;
                    unknown v = math.sin((x + t * 1.5) * 0.045) + math.sin((y - t * 1.2) * 0.04) + math.sin((x + y) * 0.02 + phase) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.08 - phase * 1.3);
                    long c = System.Convert.ToInt64((v + 4.0) * (255.0 / 8.0));
                    if (c < 0) {
                        c = 0;
                    }
                    if (c > 255) {
                        c = 255;
                    }
                    frame[System.Convert.ToInt32(row_base + x)] = c;
                }
            }
            frames.Add(bytes(frame));
        }
        save_gif(out_path, w, h, frames, grayscale_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_15_wave_interference_loop();
    }
}
