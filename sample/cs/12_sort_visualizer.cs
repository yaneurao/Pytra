using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> render(List<long> values, long w, long h)
    {
        var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
        var n = Pytra.CsModule.py_runtime.py_len(values);
        var bar_w = (w / n);
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = n;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var x0 = (long)((i * bar_w));
            var x1 = (long)(((i + 1L) * bar_w));
            if (Pytra.CsModule.py_runtime.py_bool((x1 <= x0)))
            {
                x1 = (x0 + 1L);
            }
            var bh = (long)(((Pytra.CsModule.py_runtime.py_get(values, i) / n) * h));
            var y = (h - bh);
            var __pytra_range_start_4 = y;
            var __pytra_range_stop_5 = h;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (y = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (y < __pytra_range_stop_5) : (y > __pytra_range_stop_5); y += __pytra_range_step_6)
            {
                var __pytra_range_start_7 = x0;
                var __pytra_range_stop_8 = x1;
                var __pytra_range_step_9 = 1;
                if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var x = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (x < __pytra_range_stop_8) : (x > __pytra_range_stop_8); x += __pytra_range_step_9)
                {
                    Pytra.CsModule.py_runtime.py_set(frame, ((y * w) + x), 255L);
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_12_sort_visualizer()
    {
        long w = 320L;
        long h = 180L;
        long n = 72L;
        string out_path = "sample/out/12_sort_visualizer.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<long> values = new List<long> {  };
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = n;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
        {
            Pytra.CsModule.py_runtime.py_append(values, (((i * 37L) + 19L) % n));
        }
        List<List<byte>> frames = new List<List<byte>> { render(values, w, h) };
        long op = 0L;
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = n;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
        {
            bool swapped = false;
            var __pytra_range_start_16 = 0;
            var __pytra_range_stop_17 = ((n - i) - 1L);
            var __pytra_range_step_18 = 1;
            if (__pytra_range_step_18 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var j = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (j < __pytra_range_stop_17) : (j > __pytra_range_stop_17); j += __pytra_range_step_18)
            {
                if (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_get(values, j) > Pytra.CsModule.py_runtime.py_get(values, (j + 1L)))))
                {
                    var tmp = Pytra.CsModule.py_runtime.py_get(values, j);
                    Pytra.CsModule.py_runtime.py_set(values, j, Pytra.CsModule.py_runtime.py_get(values, (j + 1L)));
                    Pytra.CsModule.py_runtime.py_set(values, (j + 1L), tmp);
                    swapped = true;
                }
                if (Pytra.CsModule.py_runtime.py_bool(((op % 8L) == 0L)))
                {
                    Pytra.CsModule.py_runtime.py_append(frames, render(values, w, h));
                }
                op = (op + 1L);
            }
            if (Pytra.CsModule.py_runtime.py_bool((!swapped)))
            {
                break;
            }
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 3L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", Pytra.CsModule.py_runtime.py_len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_12_sort_visualizer();
    }
}
