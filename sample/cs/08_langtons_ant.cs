using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> capture(List<List<int>> grid, int w, int h)
    {
        var frame = new List<byte>();
        var i = 0;
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
                // unsupported assignment: frame[i] = 255 if grid[y][x] else 0
                i = (i + 1);
            }
        }
        return bytes(frame);
    }

    public static void run_08_langtons_ant()
    {
        var w = 240;
        var h = 240;
        var out_path = "sample/out/08_langtons_ant.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<int>> grid = new List<object> {  };
        var __pytra_range_start_7 = 0;
        var __pytra_range_stop_8 = h;
        var __pytra_range_step_9 = 1;
        if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var gy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (gy < __pytra_range_stop_8) : (gy > __pytra_range_stop_8); gy += __pytra_range_step_9)
        {
            List<int> row = new List<object> {  };
            var __pytra_range_start_10 = 0;
            var __pytra_range_stop_11 = w;
            var __pytra_range_step_12 = 1;
            if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var gx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (gx < __pytra_range_stop_11) : (gx > __pytra_range_stop_11); gx += __pytra_range_step_12)
            {
                row.Add((byte)(0));
            }
            grid.Add((byte)(row));
        }
        var x = (long)Math.Floor((w) / (double)(2));
        var y = (long)Math.Floor((h) / (double)(2));
        var d = 0;
        var steps_total = 180000;
        var capture_every = 3000;
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = steps_total;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (i < __pytra_range_stop_14) : (i > __pytra_range_stop_14); i += __pytra_range_step_15)
        {
            if ((grid[y][x] == 0))
            {
                d = ((d + 1) % 4);
                // unsupported assignment: grid[y][x] = 1
            }
            else
            {
                d = ((d + 3) % 4);
                // unsupported assignment: grid[y][x] = 0
            }
            if ((d == 0))
            {
                y = (((y - 1) + h) % h);
            }
            else
            {
                if ((d == 1))
                {
                    x = ((x + 1) % w);
                }
                else
                {
                    if ((d == 2))
                    {
                        y = ((y + 1) % h);
                    }
                    else
                    {
                        x = (((x - 1) + w) % w);
                    }
                }
            }
            if (((i % capture_every) == 0))
            {
                frames.Add((byte)(capture(grid, w, h)));
            }
        }
        save_gif(out_path, w, h, frames, grayscale_palette(), delay_cs: 5, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_08_langtons_ant();
    }
}
