using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<List<int>> next_state(List<List<int>> grid, int w, int h)
    {
        List<List<int>> nxt = new List<object> {  };
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = h;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            List<int> row = new List<object> {  };
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = w;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                var cnt = 0;
                var __pytra_range_start_7 = (-1);
                var __pytra_range_stop_8 = 2;
                var __pytra_range_step_9 = 1;
                if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var dy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (dy < __pytra_range_stop_8) : (dy > __pytra_range_stop_8); dy += __pytra_range_step_9)
                {
                    var __pytra_range_start_10 = (-1);
                    var __pytra_range_stop_11 = 2;
                    var __pytra_range_step_12 = 1;
                    if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var dx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dx < __pytra_range_stop_11) : (dx > __pytra_range_stop_11); dx += __pytra_range_step_12)
                    {
                        if (((dx != 0) || (dy != 0)))
                        {
                            var nx = (((x + dx) + w) % w);
                            var ny = (((y + dy) + h) % h);
                            cnt = (cnt + grid[ny][nx]);
                        }
                    }
                }
                var alive = grid[y][x];
                if (((alive == 1) && ((cnt == 2) || (cnt == 3))))
                {
                    row.Add((byte)(1));
                }
                else
                {
                    if (((alive == 0) && (cnt == 3)))
                    {
                        row.Add((byte)(1));
                    }
                    else
                    {
                        row.Add((byte)(0));
                    }
                }
            }
            nxt.Add((byte)(row));
        }
        return nxt;
    }

    public static List<byte> render(List<List<int>> grid, int w, int h, int cell)
    {
        var width = (w * cell);
        var height = (h * cell);
        var frame = new List<byte>();
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = h;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (y < __pytra_range_stop_14) : (y > __pytra_range_stop_14); y += __pytra_range_step_15)
        {
            var __pytra_range_start_16 = 0;
            var __pytra_range_stop_17 = w;
            var __pytra_range_step_18 = 1;
            if (__pytra_range_step_18 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (x < __pytra_range_stop_17) : (x > __pytra_range_stop_17); x += __pytra_range_step_18)
            {
                var v = (grid[y][x] ? 255 : 0);
                var __pytra_range_start_19 = 0;
                var __pytra_range_stop_20 = cell;
                var __pytra_range_step_21 = 1;
                if (__pytra_range_step_21 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var yy = __pytra_range_start_19; (__pytra_range_step_21 > 0) ? (yy < __pytra_range_stop_20) : (yy > __pytra_range_stop_20); yy += __pytra_range_step_21)
                {
                    var @base = ((((y * cell) + yy) * width) + (x * cell));
                    var __pytra_range_start_22 = 0;
                    var __pytra_range_stop_23 = cell;
                    var __pytra_range_step_24 = 1;
                    if (__pytra_range_step_24 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var xx = __pytra_range_start_22; (__pytra_range_step_24 > 0) ? (xx < __pytra_range_stop_23) : (xx > __pytra_range_stop_23); xx += __pytra_range_step_24)
                    {
                        // unsupported assignment: frame[base + xx] = v
                    }
                }
            }
        }
        return bytes(frame);
    }

    public static void run_07_game_of_life_loop()
    {
        var w = 96;
        var h = 72;
        var cell = 3;
        var steps = 70;
        var out_path = "sample/out/07_game_of_life_loop.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<int>> grid = new List<object> {  };
        var __pytra_range_start_25 = 0;
        var __pytra_range_stop_26 = h;
        var __pytra_range_step_27 = 1;
        if (__pytra_range_step_27 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_25; (__pytra_range_step_27 > 0) ? (y < __pytra_range_stop_26) : (y > __pytra_range_stop_26); y += __pytra_range_step_27)
        {
            List<int> row = new List<object> {  };
            var __pytra_range_start_28 = 0;
            var __pytra_range_stop_29 = w;
            var __pytra_range_step_30 = 1;
            if (__pytra_range_step_30 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_28; (__pytra_range_step_30 > 0) ? (x < __pytra_range_stop_29) : (x > __pytra_range_stop_29); x += __pytra_range_step_30)
            {
                row.Add((byte)(((((((x * 17) + (y * 31)) + 13) % 11) < 3) ? 1 : 0)));
            }
            grid.Add((byte)(row));
        }
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_31 = 0;
        var __pytra_range_stop_32 = steps;
        var __pytra_range_step_33 = 1;
        if (__pytra_range_step_33 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var _ = __pytra_range_start_31; (__pytra_range_step_33 > 0) ? (_ < __pytra_range_stop_32) : (_ > __pytra_range_stop_32); _ += __pytra_range_step_33)
        {
            frames.Add((byte)(render(grid, w, h, cell)));
            grid = next_state(grid, w, h);
        }
        save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette(), delay_cs: 4, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", steps);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_07_game_of_life_loop();
    }
}
