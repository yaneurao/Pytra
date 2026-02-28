using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 12: Sample that outputs intermediate states of bubble sort as a GIF.
    
    public static List<byte> render(System.Collections.Generic.List<long> values, long w, long h)
    {
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(w * h);
        long n = (values).Count;
        double bar_w = w / n;
        double __hoisted_cast_1 = System.Convert.ToDouble(n);
        double __hoisted_cast_2 = System.Convert.ToDouble(h);
        long i = 0;
        for (i = 0; i < n; i += 1) {
            long x0 = Pytra.CsModule.py_runtime.py_int(i * bar_w);
            long x1 = Pytra.CsModule.py_runtime.py_int((i + 1) * bar_w);
            if (x1 <= x0) {
                x1 = x0 + 1;
            }
            long bh = Pytra.CsModule.py_runtime.py_int((Pytra.CsModule.py_runtime.py_get(values, i) / __hoisted_cast_1) * __hoisted_cast_2);
            long y = h - bh;
            for (y = y; y < h; y += 1) {
                long x = x0;
                for (x = x0; x < x1; x += 1) {
                    Pytra.CsModule.py_runtime.py_set(frame, y * w + x, 255);
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_12_sort_visualizer()
    {
        long w = 320;
        long h = 180;
        long n = 124;
        string out_path = "sample/out/12_sort_visualizer.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<long> values = new System.Collections.Generic.List<long>();
        long i = 0;
        for (i = 0; i < n; i += 1) {
            values.Add((i * 37 + 19) % n);
        }
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>> { render(values, w, h) };
        long frame_stride = 16;
        
        long op = 0;
        for (i = 0; i < n; i += 1) {
            bool swapped = false;
            long j = 0;
            for (j = 0; j < n - i - 1; j += 1) {
                if (Pytra.CsModule.py_runtime.py_get(values, j) > Pytra.CsModule.py_runtime.py_get(values, j + 1)) {
                    var __tmp_1 = (Pytra.CsModule.py_runtime.py_get(values, j + 1), Pytra.CsModule.py_runtime.py_get(values, j));
                    Pytra.CsModule.py_runtime.py_set(values, j, __tmp_1.Item1);
                    Pytra.CsModule.py_runtime.py_set(values, j + 1, __tmp_1.Item2);
                    swapped = true;
                }
                if (op % frame_stride == 0) {
                    frames.Add(render(values, w, h));
                }
                op += 1;
            }
            if (!swapped) {
                break;
            }
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_12_sort_visualizer();
    }
}
