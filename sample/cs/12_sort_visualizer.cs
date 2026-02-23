using System;
using System.Collections.Generic;
using System.Linq;

public static class Program
{
    // 12: Sample that outputs intermediate states of bubble sort as a GIF.
    
    public static List<byte> render(List<long> values, long w, long h)
    {
        List<byte> frame = bytearray((w * h));
        long n = (values).Count;
        double bar_w = (w / n);
        for (long i = 0; i < n; i += 1) {
            long x0 = Convert.ToInt64((i * bar_w));
            long x1 = Convert.ToInt64((((i + 1)) * bar_w));
            if (x1 <= x0) {
                x1 = (x0 + 1);
            }
            long bh = Convert.ToInt64((((values[(int)(i)] / n)) * h));
            long y = (h - bh);
            for (long y = y; y < h; y += 1) {
                for (long x = x0; x < x1; x += 1) {
                    frame[(int)(((y * w) + x))] = 255;
                }
            }
        }
        return bytes(frame);
    }
    
    public static void run_12_sort_visualizer()
    {
        long w = 320;
        long h = 180;
        long n = 124;
        string out_path = "sample/out/12_sort_visualizer.gif";
        
        unknown start = perf_counter();
        List<long> values = new List<unknown>();
        for (long i = 0; i < n; i += 1) {
            values.Add(((((i * 37) + 19)) % n));
        }
        List<List<byte>> frames = new List<List<byte>>();
        long frame_stride = 16;
        
        long op = 0;
        for (long i = 0; i < n; i += 1) {
            bool swapped = false;
            for (long j = 0; j < ((n - i) - 1); j += 1) {
                if (values[(int)(j)] > values[(int)((j + 1))]) {
                    var __tmp_1 = (values[(int)((j + 1))], values[(int)(j)]);
                    values[(int)(j)] = __tmp_1.Item1;
                    values[(int)((j + 1))] = __tmp_1.Item2;
                    swapped = true;
                }
                if ((op % frame_stride) == 0) {
                    frames.Add(render(values, w, h));
                }
                op += 1;
            }
            if (!swapped) {
                py_break;
            }
        }
        save_gif(out_path, w, h, frames, grayscale_palette());
        unknown elapsed = (perf_counter() - start);
        Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_12_sort_visualizer();
    }
}
