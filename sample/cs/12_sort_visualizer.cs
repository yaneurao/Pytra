using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> render(List<int> values, int w, int h)
    {
        var frame = new List<byte>();
        var n = len(values);
        var bar_w = (w / n);
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = n;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var x0 = (int)((i * bar_w));
            var x1 = (int)(((i + 1) * bar_w));
            if ((x1 <= x0))
            {
                x1 = (x0 + 1);
            }
            var bh = (int)(((values[i] / n) * h));
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
                    // unsupported assignment: frame[y * w + x] = 255
                }
            }
        }
        return bytes(frame);
    }

    public static void run_12_sort_visualizer()
    {
        var w = 320;
        var h = 180;
        var n = 72;
        var out_path = "sample/out/12_sort_visualizer.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<int> values = new List<object> {  };
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = n;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (i < __pytra_range_stop_11) : (i > __pytra_range_stop_11); i += __pytra_range_step_12)
        {
            values.Add((byte)((((i * 37) + 19) % n)));
        }
        List<List<byte>> frames = new List<object> { render(values, w, h) };
        var op = 0;
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = n;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
        {
            var swapped = false;
            var __pytra_range_start_16 = 0;
            var __pytra_range_stop_17 = ((n - i) - 1);
            var __pytra_range_step_18 = 1;
            if (__pytra_range_step_18 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var j = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (j < __pytra_range_stop_17) : (j > __pytra_range_stop_17); j += __pytra_range_step_18)
            {
                if ((values[j] > values[(j + 1)]))
                {
                    var tmp = values[j];
                    // unsupported assignment: values[j] = values[j + 1]
                    // unsupported assignment: values[j + 1] = tmp
                    swapped = true;
                }
                if (((op % 8) == 0))
                {
                    frames.Add((byte)(render(values, w, h)));
                }
                op = (op + 1);
            }
            if ((!swapped))
            {
                break;
            }
        }
        save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs: 3, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_12_sort_visualizer();
    }
}
