using System.Collections.Generic;
using System.IO;
using System;
using py_module.gif_helper;

public static class Program
{
    public static List<byte> fire_palette()
    {
        var p = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            var r = 0;
            var g = 0;
            var b = 0;
            if ((i < 85))
            {
                r = (i * 3);
                g = 0;
                b = 0;
            }
            else
            {
                if ((i < 170))
                {
                    r = 255;
                    g = ((i - 85) * 3);
                    b = 0;
                }
                else
                {
                    r = 255;
                    g = 255;
                    b = ((i - 170) * 3);
                }
            }
            p.Add((byte)(r));
            p.Add((byte)(g));
            p.Add((byte)(b));
        }
        return bytes(p);
    }

    public static void run_09_fire_simulation()
    {
        var w = 220;
        var h = 140;
        var steps = 110;
        var out_path = "sample/out/09_fire_simulation.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<int>> heat = new List<object> {  };
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = h;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var _ = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (_ < __pytra_range_stop_5) : (_ > __pytra_range_stop_5); _ += __pytra_range_step_6)
        {
            List<int> row = new List<object> {  };
            var __pytra_range_start_7 = 0;
            var __pytra_range_stop_8 = w;
            var __pytra_range_step_9 = 1;
            if (__pytra_range_step_9 == 0) throw new Exception("range() arg 3 must not be zero");
            for (_ = __pytra_range_start_7; (__pytra_range_step_9 > 0) ? (_ < __pytra_range_stop_8) : (_ > __pytra_range_stop_8); _ += __pytra_range_step_9)
            {
                row.Add((byte)(0));
            }
            heat.Add((byte)(row));
        }
        List<List<byte>> frames = new List<object> {  };
        var __pytra_range_start_10 = 0;
        var __pytra_range_stop_11 = steps;
        var __pytra_range_step_12 = 1;
        if (__pytra_range_step_12 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_10; (__pytra_range_step_12 > 0) ? (t < __pytra_range_stop_11) : (t > __pytra_range_stop_11); t += __pytra_range_step_12)
        {
            var __pytra_range_start_13 = 0;
            var __pytra_range_stop_14 = w;
            var __pytra_range_step_15 = 1;
            if (__pytra_range_step_15 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_13; (__pytra_range_step_15 > 0) ? (x < __pytra_range_stop_14) : (x > __pytra_range_stop_14); x += __pytra_range_step_15)
            {
                var val = (170 + (((x * 13) + (t * 17)) % 86));
                // unsupported assignment: heat[h - 1][x] = val
            }
            var __pytra_range_start_16 = 1;
            var __pytra_range_stop_17 = h;
            var __pytra_range_step_18 = 1;
            if (__pytra_range_step_18 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var y = __pytra_range_start_16; (__pytra_range_step_18 > 0) ? (y < __pytra_range_stop_17) : (y > __pytra_range_stop_17); y += __pytra_range_step_18)
            {
                var __pytra_range_start_19 = 0;
                var __pytra_range_stop_20 = w;
                var __pytra_range_step_21 = 1;
                if (__pytra_range_step_21 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var x = __pytra_range_start_19; (__pytra_range_step_21 > 0) ? (x < __pytra_range_stop_20) : (x > __pytra_range_stop_20); x += __pytra_range_step_21)
                {
                    var a = heat[y][x];
                    var b = heat[y][(((x - 1) + w) % w)];
                    var c = heat[y][((x + 1) % w)];
                    var d = heat[((y + 1) % h)][x];
                    var v = (long)Math.Floor(((((a + b) + c) + d)) / (double)(4));
                    var cool = (1 + (((x + y) + t) % 3));
                    var nv = (v - cool);
                    // unsupported assignment: heat[y - 1][x] = nv if nv > 0 else 0
                }
            }
            var frame = new List<byte>();
            var i = 0;
            var __pytra_range_start_22 = 0;
            var __pytra_range_stop_23 = h;
            var __pytra_range_step_24 = 1;
            if (__pytra_range_step_24 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var yy = __pytra_range_start_22; (__pytra_range_step_24 > 0) ? (yy < __pytra_range_stop_23) : (yy > __pytra_range_stop_23); yy += __pytra_range_step_24)
            {
                var __pytra_range_start_25 = 0;
                var __pytra_range_stop_26 = w;
                var __pytra_range_step_27 = 1;
                if (__pytra_range_step_27 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var xx = __pytra_range_start_25; (__pytra_range_step_27 > 0) ? (xx < __pytra_range_stop_26) : (xx > __pytra_range_stop_26); xx += __pytra_range_step_27)
                {
                    // unsupported assignment: frame[i] = heat[yy][xx]
                    i = (i + 1);
                }
            }
            frames.Add((byte)(bytes(frame)));
        }
        save_gif(out_path, w, h, frames, fire_palette(), delay_cs: 4, loop: 0);
        var elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("output:", out_path);
        Pytra.CsModule.py_runtime.print("frames:", steps);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void Main(string[] args)
    {
        run_09_fire_simulation();
    }
}
