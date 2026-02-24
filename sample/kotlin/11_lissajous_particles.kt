using math;

public static class Program
{
    // 11: Sample that outputs Lissajous-motion particles as a GIF.
    
    public static List<byte> color_palette()
    {
        List<byte> p = bytearray();
        for (long i = 0; i < 256; i += 1) {
            long r = i;
            long g = i * 3 % 256;
            long b = 255 - i;
            p.Add(r);
            p.Add(g);
            p.Add(b);
        }
        return bytes(p);
    }
    
    public static void run_11_lissajous_particles()
    {
        long w = 320;
        long h = 240;
        long frames_n = 360;
        long particles = 48;
        string out_path = "sample/out/11_lissajous_particles.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        for (long t = 0; t < frames_n; t += 1) {
            List<byte> frame = bytearray(w * h);
            for (long p = 0; p < particles; p += 1) {
                double phase = p * 0.261799;
                long x = System.Convert.ToInt64(w * 0.5 + w * 0.38 * math.sin(0.11 * t + phase * 2.0));
                long y = System.Convert.ToInt64(h * 0.5 + h * 0.38 * math.sin(0.17 * t + phase * 3.0));
                long color = 30 + p * 9 % 220;
                for (long dy = -2; dy < 3; dy += 1) {
                    for (long dx = -2; dx < 3; dx += 1) {
                        long xx = x + dx;
                        long yy = y + dy;
                        if (xx >= 0 && xx < w && yy >= 0 && yy < h) {
                            long d2 = dx * dx + dy * dy;
                            if (d2 <= 4) {
                                long idx = yy * w + xx;
                                long v = color - d2 * 20;
                                v = max(0, v);
                                if (v > frame[System.Convert.ToInt32(idx)]) {
                                    frame[System.Convert.ToInt32(idx)] = v;
                                }
                            }
                        }
                    }
                }
            }
            frames.Add(bytes(frame));
        }
        save_gif(out_path, w, h, frames, color_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_11_lissajous_particles();
    }
}
