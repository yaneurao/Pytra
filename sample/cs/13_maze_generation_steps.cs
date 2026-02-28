using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 13: Sample that outputs DFS maze-generation progress as a GIF.
    
    public static List<byte> capture(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h, long scale)
    {
        long width = w * scale;
        long height = h * scale;
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(width * height);
        long y = 0;
        for (y = 0; y < h; y += 1) {
            long x = 0;
            for (x = 0; x < w; x += 1) {
                long v = (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) == 0 ? 255 : 40);
                long yy = 0;
                for (yy = 0; yy < scale; yy += 1) {
                    long py_base = (y * scale + yy) * width + x * scale;
                    long xx = 0;
                    for (xx = 0; xx < scale; xx += 1) {
                        Pytra.CsModule.py_runtime.py_set(frame, py_base + xx, v);
                    }
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_13_maze_generation_steps()
    {
        // Increase maze size and render resolution to ensure sufficient runtime.
        long cell_w = 89;
        long cell_h = 67;
        long scale = 5;
        long capture_every = 20;
        string out_path = "sample/out/13_maze_generation_steps.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<System.Collections.Generic.List<long>> grid = (new System.Func<System.Collections.Generic.List<System.Collections.Generic.List<long>>>(() => { var __out_5 = new System.Collections.Generic.List<System.Collections.Generic.List<long>>(); foreach (var __it_6 in (new System.Func<System.Collections.Generic.List<long>>(() => { var __out_7 = new System.Collections.Generic.List<long>(); long __start_8 = System.Convert.ToInt64(0); long __stop_9 = System.Convert.ToInt64(cell_h); long __step_10 = System.Convert.ToInt64(1); if (__step_10 == 0) { return __out_7; } if (__step_10 > 0) { for (long __i_11 = __start_8; __i_11 < __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } else { for (long __i_11 = __start_8; __i_11 > __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } return __out_7; }))()) { __out_5.Add((new System.Func<System.Collections.Generic.List<long>>(() => { var __base_1 = new System.Collections.Generic.List<long> { 1 }; long __n_2 = System.Convert.ToInt64(cell_w); if (__n_2 < 0) { __n_2 = 0; } var __out_3 = new System.Collections.Generic.List<long>(); for (long __i_4 = 0; __i_4 < __n_2; __i_4 += 1) { __out_3.AddRange(__base_1); } return __out_3; }))()); } return __out_5; }))();
        System.Collections.Generic.List<(long, long)> stack = new System.Collections.Generic.List<(long, long)> { (1, 1) };
        Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, 1), 1, 0);
        
        System.Collections.Generic.List<(long, long)> dirs = new System.Collections.Generic.List<(long, long)> { (2, 0), (-2, 0), (0, 2), (0, -2) };
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        long step = 0;
        
        while (stack.Count != 0) {
            var __tmp_12 = Pytra.CsModule.py_runtime.py_get(stack, -1);
            var x = __tmp_12.Item1;
            var y = __tmp_12.Item2;
            System.Collections.Generic.List<(long, long, long, long)> candidates = new System.Collections.Generic.List<(long, long, long, long)>();
            long k = 0;
            for (k = 0; k < 4; k += 1) {
                var __tmp_13 = Pytra.CsModule.py_runtime.py_get(dirs, k);
                var dx = __tmp_13.Item1;
                var dy = __tmp_13.Item2;
                var nx = x + dx;
                var ny = y + dy;
                if ((nx >= 1) && (nx < cell_w - 1) && (ny >= 1) && (ny < cell_h - 1) && (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, ny), nx) == 1)) {
                    if (dx == 2) {
                        candidates.Add((nx, ny, x + 1, y));
                    } else {
                        if (dx == -2) {
                            candidates.Add((nx, ny, x - 1, y));
                        } else {
                            if (dy == 2) {
                                candidates.Add((nx, ny, x, y + 1));
                            } else {
                                candidates.Add((nx, ny, x, y - 1));
                            }
                        }
                    }
                }
            }
            if ((candidates).Count == 0) {
                Pytra.CsModule.py_runtime.py_pop(stack);
            } else {
                var sel = Pytra.CsModule.py_runtime.py_get(candidates, (x * 17 + y * 29 + (stack).Count * 13) % (candidates).Count);
                var __tmp_14 = sel;
                var nx = __tmp_14.Item1;
                var ny = __tmp_14.Item2;
                var wx = __tmp_14.Item3;
                var wy = __tmp_14.Item4;
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, wy), wx, 0);
                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, ny), nx, 0);
                stack.Add((nx, ny));
            }
            if (step % capture_every == 0) {
                frames.Add(capture(grid, cell_w, cell_h, scale));
            }
            step += 1;
        }
        frames.Add(capture(grid, cell_w, cell_h, scale));
        Pytra.CsModule.gif_helper.save_gif(out_path, cell_w * scale, cell_h * scale, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_13_maze_generation_steps();
    }
}
