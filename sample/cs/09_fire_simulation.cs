using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<byte> fire_palette()
    {
        var p = new List<byte>();
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = 256L;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            long r = 0L;
            long g = 0L;
            long b = 0L;
            if (Pytra.CsModule.py_runtime.py_bool((i < 85L)))
            {
                r = (i * 3L);
                g = 0L;
                b = 0L;
            }
            else
            {
                if (Pytra.CsModule.py_runtime.py_bool((i < 170L)))
                {
                    r = 255L;
                    g = ((i - 85L) * 3L);
                    b = 0L;
                }
                else
                {
                    r = 255L;
                    g = 255L;
                    b = ((i - 170L) * 3L);
                }
            }
            Pytra.CsModule.py_runtime.py_append(p, r);
            Pytra.CsModule.py_runtime.py_append(p, g);
            Pytra.CsModule.py_runtime.py_append(p, b);
        }
        return Pytra.CsModule.py_runtime.py_bytes(p);
    }

    public static void run_09_fire_simulation()
    {
        long w = 380L;
        long h = 260L;
        long steps = 420L;
        string out_path = "sample/out/09_fire_simulation.gif";
        var start = Pytra.CsModule.time.perf_counter();
        List<List<long>> heat = new List<List<long>> {  };
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = h;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var __pytra_unused_7 = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (__pytra_unused_7 < __pytra_range_stop_5) : (__pytra_unused_7 > __pytra_range_stop_5); __pytra_unused_7 += __pytra_range_step_6)
        {
            List<long> row = new List<long> {  };
            var __pytra_range_start_8 = 0;
            var __pytra_range_stop_9 = w;
            var __pytra_range_step_10 = 1;
            if (__pytra_range_step_10 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var __pytra_unused_11 = __pytra_range_start_8; (__pytra_range_step_10 > 0) ? (__pytra_unused_11 < __pytra_range_stop_9) : (__pytra_unused_11 > __pytra_range_stop_9); __pytra_unused_11 += __pytra_range_step_10)
            {
                Pytra.CsModule.py_runtime.py_append(row, 0L);
            }
            Pytra.CsModule.py_runtime.py_append(heat, row);
        }
        List<List<byte>> frames = new List<List<byte>> {  };
        var __pytra_range_start_12 = 0;
        var __pytra_range_stop_13 = steps;
        var __pytra_range_step_14 = 1;
        if (__pytra_range_step_14 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var t = __pytra_range_start_12; (__pytra_range_step_14 > 0) ? (t < __pytra_range_stop_13) : (t > __pytra_range_stop_13); t += __pytra_range_step_14)
        {
            var __pytra_range_start_15 = 0;
            var __pytra_range_stop_16 = w;
            var __pytra_range_step_17 = 1;
            if (__pytra_range_step_17 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var x = __pytra_range_start_15; (__pytra_range_step_17 > 0) ? (x < __pytra_range_stop_16) : (x > __pytra_range_stop_16); x += __pytra_range_step_17)
            {
                var val = (170L + (((x * 13L) + (t * 17L)) % 86L));
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(heat, (h - 1L)), x, val);
            }
            var __pytra_range_start_18 = 1L;
            var __pytra_range_stop_19 = h;
            var __pytra_range_step_20 = 1;
            if (__pytra_range_step_20 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var y = __pytra_range_start_18; (__pytra_range_step_20 > 0) ? (y < __pytra_range_stop_19) : (y > __pytra_range_stop_19); y += __pytra_range_step_20)
            {
                var __pytra_range_start_21 = 0;
                var __pytra_range_stop_22 = w;
                var __pytra_range_step_23 = 1;
                if (__pytra_range_step_23 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var x = __pytra_range_start_21; (__pytra_range_step_23 > 0) ? (x < __pytra_range_stop_22) : (x > __pytra_range_stop_22); x += __pytra_range_step_23)
                {
                    var a = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), x);
                    var b = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), (((x - 1L) + w) % w));
                    var c = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, y), ((x + 1L) % w));
                    var d = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, ((y + 1L) % h)), x);
                    var v = (long)Math.Floor(((((a + b) + c) + d)) / (double)(4L));
                    var cool = (1L + (((x + y) + t) % 3L));
                    var nv = (v - cool);
                    Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(heat, (y - 1L)), x, (Pytra.CsModule.py_runtime.py_bool((nv > 0L)) ? nv : 0L));
                }
            }
            var frame = Pytra.CsModule.py_runtime.py_bytearray((w * h));
            long i = 0L;
            var __pytra_range_start_24 = 0;
            var __pytra_range_stop_25 = h;
            var __pytra_range_step_26 = 1;
            if (__pytra_range_step_26 == 0) throw new Exception("range() arg 3 must not be zero");
            for (var yy = __pytra_range_start_24; (__pytra_range_step_26 > 0) ? (yy < __pytra_range_stop_25) : (yy > __pytra_range_stop_25); yy += __pytra_range_step_26)
            {
                var __pytra_range_start_27 = 0;
                var __pytra_range_stop_28 = w;
                var __pytra_range_step_29 = 1;
                if (__pytra_range_step_29 == 0) throw new Exception("range() arg 3 must not be zero");
                for (var xx = __pytra_range_start_27; (__pytra_range_step_29 > 0) ? (xx < __pytra_range_stop_28) : (xx > __pytra_range_stop_28); xx += __pytra_range_step_29)
                {
                    Pytra.CsModule.py_runtime.py_set(frame, i, Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(heat, yy), xx));
                    i = (i + 1L);
                }
            }
            Pytra.CsModule.py_runtime.py_append(frames, Pytra.CsModule.py_runtime.py_bytes(frame));
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w, h, frames, fire_palette(), delay_cs: 4L, loop: 0L);
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
