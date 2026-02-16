using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> capture(List<List<int>> grid, int w, int h, int scale)
    {
        var width = (w * scale);
        var height = (h * scale);
        var frame = new List<byte>();
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
                var v = ((grid[y][x] == 0) ? 255 : 40);
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
                        // unsupported assignment: frame[base + xx] = v
                    }
                }
            }
        }
        return bytes(frame);
    }

    public static void run_13_maze_generation_steps()
    {
        var cell_w = 61;
        var cell_h = 45;
        var scale = 4;
        var out_path = "sample/out/13_maze_generation_steps.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<int>> grid = new List<object> {  };
        var __pytra_range_start_13 = 0;
        var __pytra_range_stop_14 = cell_h;
        var __pytra_range_step_15 = 1;
        if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var _ = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (_ < __pytra_range_stop_14) : (_ > __pytra_range_stop_14); _ += __pytra_range_step_15)
        {
            List<int> row = new List<object> {  };
            var __pytra_range_start_16 = 0;
            var __pytra_range_stop_17 = cell_w;
            var __pytra_range_step_18 = 1;
            if (__pytra_range_step_18 == 0) throw new Exception("range() arg 3 must not be zero");
            for (_ = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (_ < __pytra_range_stop_17) : (_ > __pytra_range_stop_17); _ += __pytra_range_step_18)
            {
                row.Add((byte)(1));
            }
            grid.Add((byte)(row));
        }
        List<Tuple<int, int>> stack = new List<object> { Tuple.Create(1, 1) };
        // unsupported assignment: grid[1][1] = 0
        List<Tuple<int, int>> dirs = new List<object> { Tuple.Create(2, 0), Tuple.Create((-2), 0), Tuple.Create(0, 2), Tuple.Create(0, (-2)) };
        List<List<byte>> frames = new List<object> {  };
        var step = 0;
        while ((len(stack) > 0))
        {
            var last_index = (len(stack) - 1);
            var _tmp_tuple = stack[last_index];
            var x = _tmp_tuple.Item1;
            var y = _tmp_tuple.Item2;
            List<Tuple<int, int, int, int>> candidates = new List<object> {  };
            var __pytra_range_start_19 = 0;
            var __pytra_range_stop_20 = 4;
            var __pytra_range_step_21 = 1;
            if (__pytra_range_step_21 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var k = __pytra_range_start_19; (__pytra_range_step_21 > 0) ? (k < __pytra_range_stop_20) : (k > __pytra_range_stop_20); k += __pytra_range_step_21)
            {
                var _tmp_tuple = dirs[k];
                var dx = _tmp_tuple.Item1;
                var dy = _tmp_tuple.Item2;
                var nx = (x + dx);
                var ny = (y + dy);
                if (((nx >= 1) && (nx < (cell_w - 1)) && (ny >= 1) && (ny < (cell_h - 1)) && (grid[ny][nx] == 1)))
                {
                    if ((dx == 2))
                    {
                        candidates.Add((byte)(Tuple.Create(nx, ny, (x + 1), y)));
                    }
                    else
                    {
                        if ((dx == (-2)))
                        {
                            candidates.Add((byte)(Tuple.Create(nx, ny, (x - 1), y)));
                        }
                        else
                        {
                            if ((dy == 2))
                            {
                                candidates.Add((byte)(Tuple.Create(nx, ny, x, (y + 1))));
                            }
                            else
                            {
                                candidates.Add((byte)(Tuple.Create(nx, ny, x, (y - 1))));
                            }
                        }
                    }
                }
            }
            if ((len(candidates) == 0))
            {
                stack.pop();
            }
            else
            {
                var sel = candidates[((((x * 17) + (y * 29)) + (len(stack) * 13)) % len(candidates))];
                var _tmp_tuple = sel;
                var nx = _tmp_tuple.Item1;
                var ny = _tmp_tuple.Item2;
                var wx = _tmp_tuple.Item3;
                var wy = _tmp_tuple.Item4;
                // unsupported assignment: grid[wy][wx] = 0
                // unsupported assignment: grid[ny][nx] = 0
                stack.Add((byte)(Tuple.Create(nx, ny)));
            }
            if (((step % 25) == 0))
            {
                frames.Add((byte)(capture(grid, cell_w, cell_h, scale)));
            }
            step = (step + 1);
        }
        frames.Add((byte)(capture(grid, cell_w, cell_h, scale)));
        save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette(), delay_cs: 4, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", len(frames));
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_13_maze_generation_steps();
    }
}
