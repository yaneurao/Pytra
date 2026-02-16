using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> capture(List<List<long>> grid, long w, long h, long scale)
    {
        var width = (w * scale);
        var height = (h * scale);
        var frame = Pytra.CsModule.py_runtime.py_bytearray((width * height));
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
                var v = (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) == 0L)) ? 255L : 40L);
                var __pytra_range_start_7 = 0;
                var __pytra_range_stop_8 = scale;
                var __pytra_range_step_9 = 1;
                if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var yy = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (yy < __pytra_range_stop_8) : (yy > __pytra_range_stop_8); yy += __pytra_range_step_9)
                {
                    var @base = ((((y * scale) + yy) * width) + (x * scale));
                    var __pytra_range_start_10 = 0;
                    var __pytra_range_stop_11 = scale;
                    var __pytra_range_step_12 = 1;
                    if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
                    for (var xx = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (xx < __pytra_range_stop_11) : (xx > __pytra_range_stop_11); xx += __pytra_range_step_12)
                    {
                        Pytra.CsModule.py_runtime.py_set(frame, (@base + xx), v);
                    }
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }

    public static void run_13_maze_generation_steps()
    {
        long cell_w = 61L;
        long cell_h = 45L;
        long scale = 4L;
        string out_path = "sample/out/13_maze_generation_steps.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<long>> grid = new List<List<long>> {  };
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = cell_h;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var __pytra_unused_16 = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (__pytra_unused_16 < __pytra_range_stop_14) : (__pytra_unused_16 > __pytra_range_stop_14); __pytra_unused_16 += __pytra_range_step_15)
        {
            List<long> row = new List<long> {  };
            var __pytra_range_start_17 = 0;
            var __pytra_range_stop_18 = cell_w;
            var __pytra_range_step_19 = 1;
            if (__pytra_range_step_19 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var __pytra_unused_20 = __pytra_range_start_17; (__pytra_range_step_19 > 0) ? (__pytra_unused_20 < __pytra_range_stop_18) : (__pytra_unused_20 > __pytra_range_stop_18); __pytra_unused_20 += __pytra_range_step_19)
            {
                Pytra.CsModule.py_runtime.py_append(row, 1L);
            }
            Pytra.CsModule.py_runtime.py_append(grid, row);
        }
        List<Tuple<long, long>> stack = new List<Tuple<long, long>> { Tuple.Create(1L, 1L) };
        Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, 1L), 1L, 0L);
        List<Tuple<long, long>> dirs = new List<Tuple<long, long>> { Tuple.Create(2L, 0L), Tuple.Create((-2L), 0L), Tuple.Create(0L, 2L), Tuple.Create(0L, (-2L)) };
        List<List<byte>> frames = new List<List<byte>> {  };
        long step = 0L;
        while (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_len(stack) > 0L)))
        {
            var last_index = (Pytra.CsModule.py_runtime.py_len(stack) - 1L);
            var __pytra_tuple_21 = Pytra.CsModule.py_runtime.py_get(stack, last_index);
            var x = __pytra_tuple_21.Item1;
            var y = __pytra_tuple_21.Item2;
            List<Tuple<long, long, long, long>> candidates = new List<Tuple<long, long, long, long>> {  };
            var __pytra_range_start_22 = 0;
            var __pytra_range_stop_23 = 4L;
            var __pytra_range_step_24 = 1;
            if (__pytra_range_step_24 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var k = __pytra_range_start_22; (__pytra_range_step_24 > 0) ? (k < __pytra_range_stop_23) : (k > __pytra_range_stop_23); k += __pytra_range_step_24)
            {
                var __pytra_tuple_25 = Pytra.CsModule.py_runtime.py_get(dirs, k);
                var dx = __pytra_tuple_25.Item1;
                var dy = __pytra_tuple_25.Item2;
                var nx = (x + dx);
                var ny = (y + dy);
                if (Pytra.CsModule.py_runtime.py_bool(((nx >= 1L) && (nx < (cell_w - 1L)) && (ny >= 1L) && (ny < (cell_h - 1L)) && (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, ny), nx) == 1L))))
                {
                    if (Pytra.CsModule.py_runtime.py_bool((dx == 2L)))
                    {
                        Pytra.CsModule.py_runtime.py_append(candidates, Tuple.Create(nx, ny, (x + 1L), y));
                    }
                    else
                    {
                        if (Pytra.CsModule.py_runtime.py_bool((dx == (-2L))))
                        {
                            Pytra.CsModule.py_runtime.py_append(candidates, Tuple.Create(nx, ny, (x - 1L), y));
                        }
                        else
                        {
                            if (Pytra.CsModule.py_runtime.py_bool((dy == 2L)))
                            {
                                Pytra.CsModule.py_runtime.py_append(candidates, Tuple.Create(nx, ny, x, (y + 1L)));
                            }
                            else
                            {
                                Pytra.CsModule.py_runtime.py_append(candidates, Tuple.Create(nx, ny, x, (y - 1L)));
                            }
                        }
                    }
                }
            }
            if (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_len(candidates) == 0L)))
            {
                Pytra.CsModule.py_runtime.py_pop(stack);
            }
            else
            {
                var sel = Pytra.CsModule.py_runtime.py_get(candidates, ((((x * 17L) + (y * 29L)) + (Pytra.CsModule.py_runtime.py_len(stack) * 13L)) % Pytra.CsModule.py_runtime.py_len(candidates)));
                var __pytra_tuple_26 = sel;
                var nx = __pytra_tuple_26.Item1;
                var ny = __pytra_tuple_26.Item2;
                var wx = __pytra_tuple_26.Item3;
                var wy = __pytra_tuple_26.Item4;
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, wy), wx, 0L);
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, ny), nx, 0L);
                Pytra.CsModule.py_runtime.py_append(stack, Tuple.Create(nx, ny));
            }
            if (Pytra.CsModule.py_runtime.py_bool(((step % 25L) == 0L)))
            {
                Pytra.CsModule.py_runtime.py_append(frames, capture(grid, cell_w, cell_h, scale));
            }
            step = (step + 1L);
        }
        Pytra.CsModule.py_runtime.py_append(frames, capture(grid, cell_w, cell_h, scale));
        Pytra.CsModule.gif_helper.save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, Pytra.CsModule.gif_helper.grayscale_palette(), delay_cs: 4L, loop: 0L);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", Pytra.CsModule.py_runtime.py_len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_13_maze_generation_steps();
    }
}
