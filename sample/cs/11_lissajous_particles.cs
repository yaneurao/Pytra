using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;
using math = Pytra.CsModule.math;

public static class Program
{
    // 11: Sample that outputs Lissajous-motion particles as a GIF.
    
    public static List<byte> color_palette()
    {
        List<byte> p = new System.Collections.Generic.List<byte>();
        long i = 0;
        for (i = 0; i < 256; i += 1) {
            long r = i;
            long g = i * 3 % 256;
            long b = 255 - i;
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }
    
    public static void run_11_lissajous_particles()
    {
        long w = 320;
        long h = 240;
        long frames_n = 360;
        long particles = 48;
        string out_path = "sample/out/11_lissajous_particles.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        
        long t = 0;
        for (t = 0; t < frames_n; t += 1) {
            List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
            double __hoisted_cast_1 = System.Convert.ToDouble(t);
            
            long p = 0;
            for (p = 0; p < particles; p += 1) {
                double phase = p * 0.261799;
                long x = Pytra.CsModule.py_runtime.py_int(w * 0.5 + w * 0.38 * Pytra.CsModule.math.sin(0.11 * __hoisted_cast_1 + phase * 2.0));
                long y = Pytra.CsModule.py_runtime.py_int(h * 0.5 + h * 0.38 * Pytra.CsModule.math.sin(0.17 * __hoisted_cast_1 + phase * 3.0));
                long color = 30 + p * 9 % 220;
                
                long dy = -2;
                for (dy = -2; dy < 3; dy += 1) {
                    long dx = -2;
                    for (dx = -2; dx < 3; dx += 1) {
                        long xx = x + dx;
                        long yy = y + dy;
                        if ((xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)) {
                            long d2 = dx * dx + dy * dy;
                            if (d2 <= 4) {
                                long idx = yy * w + xx;
                                long v = color - d2 * 20;
                                v = System.Convert.ToInt64(System.Math.Max(0, v));
                                if (v > Pytra.CsModule.py_runtime.py_get(frame, idx)) {
                                    Pytra.CsModule.py_runtime.py_set(frame, idx, System.Convert.ToInt64(v));
                                }
                            }
                        }
                    }
                }
            }
            frames.Add(Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, color_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_11_lissajous_particles();
    }
}
