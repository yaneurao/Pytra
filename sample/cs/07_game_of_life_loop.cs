using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<List<long>> next_state(List<List<long>> grid, long w, long h)
    {
        List<List<long>> nxt = new List<List<long>> {  };
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = h;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
        {
            List<long> row = new List<long> {  };
            var __pytra_range_start_4 = 0;
            var __pytra_range_stop_5 = w;
            var __pytra_range_step_6 = 1;
            if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
            {
                long cnt = 0L;
                var __pytra_range_start_7 = (-1L);
                var __pytra_range_stop_8 = 2L;
                var __pytra_range_step_9 = 1;
                if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var dy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (dy < __pytra_range_stop_8) : (dy > __pytra_range_stop_8); dy += __pytra_range_step_9)
                {
                    var __pytra_range_start_10 = (-1L);
                    var __pytra_range_stop_11 = 2L;
                    var __pytra_range_step_12 = 1;
                    if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var dx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (dx < __pytra_range_stop_11) : (dx > __pytra_range_stop_11); dx += __pytra_range_step_12)
                    {
                        if (Pytra.CsModule.py_runtime.py_bool(((dx != 0L) || (dy != 0L))))
                        {
                            var nx = (((x + dx) + w) % w);
                            var ny = (((y + dy) + h) % h);
                            cnt = (cnt + Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, ny), nx));
                        }
                    }
                }
                var alive = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x);
                if (Pytra.CsModule.py_runtime.py_bool(((alive == 1L) && ((cnt == 2L) || (cnt == 3L)))))
                {
                    Pytra.CsModule.py_runtime.py_append(row, 1L);
                }
                else
                {
                    if (Pytra.CsModule.py_runtime.py_bool(((alive == 0L) && (cnt == 3L))))
                    {
                        Pytra.CsModule.py_runtime.py_append(row, 1L);
                    }
                    else
                    {
                        Pytra.CsModule.py_runtime.py_append(row, 0L);
                    }
                }
            }
            Pytra.CsModule.py_runtime.py_append(nxt, row);
        }
        return nxt;
    }

    public static List<byte> render(List<List<long>> grid, long w, long h, long cell)
    {
        var width = (w * cell);
        var height = (h * cell);
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
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
                var v = (Pytra.CsModule.py_runtime.py_bool(Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x)) ? 255L : 0L);
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
                        Pytra.CsModule.py_runtime.py_set(frame, (@base + xx), v);
                    }
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_07_game_of_life_loop()
    {
        long w = 144L;
        long h = 108L;
        long cell = 4L;
        long steps = 210L;
        string out_path = "sample/out/07_game_of_life_loop.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<long>> grid = new List<List<long>> {  };
        var __pytra_range_start_25 = 0;
        var __pytra_range_stop_26 = h;
        var __pytra_range_step_27 = 1;
        if (__pytra_range_step_27 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var y = __pytra_range_start_25; (__pytra_range_step_27 > 0) ? (y < __pytra_range_stop_26) : (y > __pytra_range_stop_26); y += __pytra_range_step_27)
        {
            List<long> row = new List<long> {  };
            var __pytra_range_start_28 = 0;
            var __pytra_range_stop_29 = w;
            var __pytra_range_step_30 = 1;
            if (__pytra_range_step_30 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_28; (__pytra_range_step_30 > 0) ? (x < __pytra_range_stop_29) : (x > __pytra_range_stop_29); x += __pytra_range_step_30)
            {
                Pytra.CsModule.py_runtime.py_append(row, (Pytra.CsModule.py_runtime.py_bool((((((x * 17L) + (y * 31L)) + 13L) % 11L) < 3L)) ? 1L : 0L));
            }
            Pytra.CsModule.py_runtime.py_append(grid, row);
        }
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_31 = 0;
        var __pytra_range_stop_32 = steps;
        var __pytra_range_step_33 = 1;
        if (__pytra_range_step_33 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var __pytra_unused_34 = __pytra_range_start_31; (__pytra_range_step_33 > 0) ? (__pytra_unused_34 < __pytra_range_stop_32) : (__pytra_unused_34 > __pytra_range_stop_32); __pytra_unused_34 += __pytra_range_step_33)
        {
            Pytra.CsModule.py_runtime.py_append(frames, render(grid, w, h, cell));
            grid = next_state(grid, w, h);
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, (w * cell), (h * cell), frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 4L, loop: 0L);
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
