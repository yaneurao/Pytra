using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> capture(List<List<long>> grid, long w, long h)
    {
        var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
        long i = 0L;
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = h;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = w;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                Pytra.CsModule.py_runtime.py_set(frame, i, (Pytra.CsModule.py_runtime.py_bool(Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x)) ? 255L : 0L));
                i = (i + 1L);
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_08_langtons_ant()
    {
        long w = 240L;
        long h = 240L;
        string out_path = "sample/out/08_langtons_ant.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<long>> grid = new List<List<long>> {  };
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = h;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var gy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (gy < __pytra_range_stop_8) : (gy > __pytra_range_stop_8); gy += __pytra_range_step_9)
        {
            List<long> row = new List<long> {  };
            var __pytra_range_start_10 = 0;
            var __pytra_range_stop_11 = w;
            var __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var gx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (gx < __pytra_range_stop_11) : (gx > __pytra_range_stop_11); gx += __pytra_range_step_12)
            {
                Pytra.CsModule.py_runtime.py_append(row, 0L);
            }
            Pytra.CsModule.py_runtime.py_append(grid, row);
        }
        var x = (long)Math.Floor((w) / (double)(2L));
        var y = (long)Math.Floor((h) / (double)(2L));
        long d = 0L;
        long steps_total = 180000L;
        long capture_every = 3000L;
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = steps_total;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
        {
            if (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) == 0L)))
            {
                d = ((d + 1L) % 4L);
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, y), x, 1L);
            }
            else
            {
                d = ((d + 3L) % 4L);
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, y), x, 0L);
            }
            if (Pytra.CsModule.py_runtime.py_bool((d == 0L)))
            {
                y = (((y - 1L) + h) % h);
            }
            else
            {
                if (Pytra.CsModule.py_runtime.py_bool((d == 1L)))
                {
                    x = ((x + 1L) % w);
                }
                else
                {
                    if (Pytra.CsModule.py_runtime.py_bool((d == 2L)))
                    {
                        y = ((y + 1L) % h);
                    }
                    else
                    {
                        x = (((x - 1L) + w) % w);
                    }
                }
            }
            if (Pytra.CsModule.py_runtime.py_bool(((i % capture_every) == 0L)))
            {
                Pytra.CsModule.py_runtime.py_append(frames, capture(grid, w, h));
            }
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 5L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", Pytra.CsModule.py_runtime.py_len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_08_langtons_ant();
    }
}
