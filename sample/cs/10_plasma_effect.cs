using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using math = Pytra.CsModule.math;

public static class Program
{
    // 10: Sample that outputs a plasma effect as a GIF.
    
    public static void run_10_plasma_effect()
    {
        long w = 320;
        long h = 240;
        long frames_n = 216;
        string out_path = "sample/out/10_plasma_effect.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        
        long t = 0;
        for (t = 0; t < frames_n; t += 1) {
            List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
            long y = 0;
            for (y = 0; y < h; y += 1) {
                long row_base = y * w;
                long x = 0;
                for (x = 0; x < w; x += 1) {
                    long dx = x - 160;
                    long dy = y - 120;
                    var v = Pytra.CsModule.math.sin((x + t * 2.0) * 0.045) + Pytra.CsModule.math.sin((y - t * 1.2) * 0.05) + Pytra.CsModule.math.sin((x + y + t * 1.7) * 0.03) + Pytra.CsModule.math.sin(Pytra.CsModule.math.sqrt(dx * dx + dy * dy) * 0.07 - t * 0.18);
                    long c = Pytra.CsModule.py_runtime.py_int((v + 4.0) * (255.0 / 8.0));
                    if (c < 0) {
                        c = 0;
                    }
                    if (c > 255) {
                        c = 255;
                    }
                    Pytra.CsModule.py_runtime.py_set(frame, row_base + x, c);
                }
            }
            frames.Add(Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_10_plasma_effect();
    }
}
