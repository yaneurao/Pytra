using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 07: Sample that outputs Game of Life evolution as a GIF.
    
    public static System.Collections.Generic.List<System.Collections.Generic.List<long>> next_state(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h)
    {
        System.Collections.Generic.List<System.Collections.Generic.List<long>> nxt = new System.Collections.Generic.List<System.Collections.Generic.List<long>>();
        long y = 0;
        for (y = 0; y < h; y += 1) {
            System.Collections.Generic.List<long> row = new System.Collections.Generic.List<long>();
            long x = 0;
            for (x = 0; x < w; x += 1) {
                long cnt = 0;
                long dy = -1;
                for (dy = -1; dy < 2; dy += 1) {
                    long dx = -1;
                    for (dx = -1; dx < 2; dx += 1) {
                        if ((dx != 0) || (dy != 0)) {
                            long nx = (x + dx + w) % w;
                            long ny = (y + dy + h) % h;
                            cnt += Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, ny), nx);
                        }
                    }
                }
                long alive = Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x);
                if ((alive == 1) && (((cnt == 2) || (cnt == 3)))) {
                    row.Add(1);
                } else {
                    if ((alive == 0) && (cnt == 3)) {
                        row.Add(1);
                    } else {
                        row.Add(0);
                    }
                }
            }
            nxt.Add(row);
        }
        return nxt;
    }
    
    public static List<byte> render(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h, long cell)
    {
        long width = w * cell;
        long height = h * cell;
        List<byte> frame = Pytra.CsModule.py_runtime.py_bytearray(width * height);
        long y = 0;
        for (y = 0; y < h; y += 1) {
            long x = 0;
            for (x = 0; x < w; x += 1) {
                long v = (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(grid, y), x) != 0 ? 255 : 0);
                long yy = 0;
                for (yy = 0; yy < cell; yy += 1) {
                    long py_base = (y * cell + yy) * width + x * cell;
                    long xx = 0;
                    for (xx = 0; xx < cell; xx += 1) {
                        Pytra.CsModule.py_runtime.py_set(frame, py_base + xx, v);
                    }
                }
            }
        }
        return Pytra.CsModule.py_runtime.py_bytes(frame);
    }
    
    public static void run_07_game_of_life_loop()
    {
        long w = 144;
        long h = 108;
        long cell = 4;
        long steps = 105;
        string out_path = "sample/out/07_game_of_life_loop.gif";
        
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<System.Collections.Generic.List<long>> grid = (new System.Func<System.Collections.Generic.List<System.Collections.Generic.List<long>>>(() => { var __out_5 = new System.Collections.Generic.List<System.Collections.Generic.List<long>>(); foreach (var __it_6 in (new System.Func<System.Collections.Generic.List<long>>(() => { var __out_7 = new System.Collections.Generic.List<long>(); long __start_8 = System.Convert.ToInt64(0); long __stop_9 = System.Convert.ToInt64(h); long __step_10 = System.Convert.ToInt64(1); if (__step_10 == 0) { return __out_7; } if (__step_10 > 0) { for (long __i_11 = __start_8; __i_11 < __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } else { for (long __i_11 = __start_8; __i_11 > __stop_9; __i_11 += __step_10) { __out_7.Add(__i_11); } } return __out_7; }))()) { __out_5.Add((new System.Func<System.Collections.Generic.List<long>>(() => { var __base_1 = new System.Collections.Generic.List<long> { 0 }; long __n_2 = System.Convert.ToInt64(w); if (__n_2 < 0) { __n_2 = 0; } var __out_3 = new System.Collections.Generic.List<long>(); for (long __i_4 = 0; __i_4 < __n_2; __i_4 += 1) { __out_3.AddRange(__base_1); } return __out_3; }))()); } return __out_5; }))();
        
        // Lay down sparse noise so the whole field is less likely to stabilize too early.
        // Avoid large integer literals so all transpilers handle the expression consistently.
        long y = 0;
        for (y = 0; y < h; y += 1) {
            long x = 0;
            for (x = 0; x < w; x += 1) {
                long noise = (x * 37 + y * 73 + x * y % 19 + (x + y) % 11) % 97;
                if (noise < 3) {
                    Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, y), x, 1);
                }
            }
        }
        // Place multiple well-known long-lived patterns.
        System.Collections.Generic.List<System.Collections.Generic.List<long>> glider = new System.Collections.Generic.List<System.Collections.Generic.List<long>> { new System.Collections.Generic.List<long> { 0, 1, 0 }, new System.Collections.Generic.List<long> { 0, 0, 1 }, new System.Collections.Generic.List<long> { 1, 1, 1 } };
        System.Collections.Generic.List<System.Collections.Generic.List<long>> r_pentomino = new System.Collections.Generic.List<System.Collections.Generic.List<long>> { new System.Collections.Generic.List<long> { 0, 1, 1 }, new System.Collections.Generic.List<long> { 1, 1, 0 }, new System.Collections.Generic.List<long> { 0, 1, 0 } };
        System.Collections.Generic.List<System.Collections.Generic.List<long>> lwss = new System.Collections.Generic.List<System.Collections.Generic.List<long>> { new System.Collections.Generic.List<long> { 0, 1, 1, 1, 1 }, new System.Collections.Generic.List<long> { 1, 0, 0, 0, 1 }, new System.Collections.Generic.List<long> { 0, 0, 0, 0, 1 }, new System.Collections.Generic.List<long> { 1, 0, 0, 1, 0 } };
        
        long gy = 8;
        for (gy = 8; gy < h - 8; gy += 18) {
            long gx = 8;
            for (gx = 8; gx < w - 8; gx += 22) {
                long kind = (gx * 7 + gy * 11) % 3;
                if (kind == 0) {
                    long ph = (glider).Count;
                    long py = 0;
                    for (py = 0; py < ph; py += 1) {
                        long pw = (Pytra.CsModule.py_runtime.py_get(glider, py)).Count;
                        long px = 0;
                        for (px = 0; px < pw; px += 1) {
                            if (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(glider, py), px) == 1) {
                                Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, (gy + py) % h), (gx + px) % w, 1);
                            }
                        }
                    }
                } else {
                    if (kind == 1) {
                        long ph = (r_pentomino).Count;
                        long py = 0;
                        for (py = 0; py < ph; py += 1) {
                            long pw = (Pytra.CsModule.py_runtime.py_get(r_pentomino, py)).Count;
                            long px = 0;
                            for (px = 0; px < pw; px += 1) {
                                if (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(r_pentomino, py), px) == 1) {
                                    Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, (gy + py) % h), (gx + px) % w, 1);
                                }
                            }
                        }
                    } else {
                        long ph = (lwss).Count;
                        long py = 0;
                        for (py = 0; py < ph; py += 1) {
                            long pw = (Pytra.CsModule.py_runtime.py_get(lwss, py)).Count;
                            long px = 0;
                            for (px = 0; px < pw; px += 1) {
                                if (Pytra.CsModule.py_runtime.py_get(Pytra.CsModule.py_runtime.py_get(lwss, py), px) == 1) {
                                    Pytra.CsModule.py_runtime.py_set(Pytra.CsModule.py_runtime.py_get(grid, (gy + py) % h), (gx + px) % w, 1);
                                }
                            }
                        }
                    }
                }
            }
        }
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<List<byte>>();
        long _ = 0;
        for (_ = 0; _ < steps; _ += 1) {
            frames.Add(render(grid, w, h, cell));
            grid = next_state(grid, w, h);
        }
        Pytra.CsModule.gif_helper.save_gif(out_path, w * cell, h * cell, frames, Pytra.CsModule.gif_helper.grayscale_palette());
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", steps }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_07_game_of_life_loop();
    }
}
