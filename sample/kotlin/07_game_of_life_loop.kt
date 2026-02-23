// このファイルは EAST ベース Kotlin プレビュー出力です。
// TODO: 専用 KotlinEmitter 実装へ段階移行する。
fun main() {
    /*
    using System;
    using System.Collections.Generic;
    using System.Linq;
    
    public static class Program
    {
        // 07: Sample that outputs Game of Life evolution as a GIF.
        
        public static List<List<long>> next_state(List<List<long>> grid, long w, long h)
        {
            List<List<long>> nxt = new List<unknown>();
            for (long y = 0; y < h; y += 1) {
                List<long> row = new List<unknown>();
                for (long x = 0; x < w; x += 1) {
                    long cnt = 0;
                    for (long dy = (-1); dy < 2; dy += 1) {
                        for (long dx = (-1); dx < 2; dx += 1) {
                            if ((dx != 0) || (dy != 0)) {
                                long nx = ((((x + dx) + w)) % w);
                                long ny = ((((y + dy) + h)) % h);
                                cnt += grid[(int)(ny)][(int)(nx)];
                            }
                        }
                    }
                    long alive = grid[(int)(y)][(int)(x)];
                    if ((alive == 1) && ((cnt == 2) || (cnt == 3))) {
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
        
        public static List<byte> render(List<List<long>> grid, long w, long h, long cell)
        {
            long width = (w * cell);
            long height = (h * cell);
            List<byte> frame = bytearray((width * height));
            for (long y = 0; y < h; y += 1) {
                for (long x = 0; x < w; x += 1) {
                    long v = (grid[(int)(y)][(int)(x)] ? 255 : 0);
                    for (long yy = 0; yy < cell; yy += 1) {
                        long py_base = (((((y * cell) + yy)) * width) + (x * cell));
                        for (long xx = 0; xx < cell; xx += 1) {
                            frame[(int)((py_base + xx))] = v;
                        }
                    }
                }
            }
            return bytes(frame);
        }
        
        public static void run_07_game_of_life_loop()
        {
            long w = 144;
            long h = 108;
            long cell = 4;
            long steps = 105;
            string out_path = "sample/out/07_game_of_life_loop.gif";
            
            unknown start = perf_counter();
            List<List<long>> grid = [[0] * w for _ in range(h)];
            
            // Lay down sparse noise so the whole field is less likely to stabilize too early.
            // Avoid large integer literals so all transpilers handle the expression consistently.
            for (long y = 0; y < h; y += 1) {
                for (long x = 0; x < w; x += 1) {
                    long noise = ((((((x * 37) + (y * 73)) + ((x * y) % 19)) + (((x + y)) % 11))) % 97);
                    if (noise < 3) {
                        grid[(int)(y)][(int)(x)] = 1;
                    }
                }
            }
            // Place multiple well-known long-lived patterns.
            List<List<long>> glider = new List<List<long>>();
            List<List<long>> r_pentomino = new List<List<long>>();
            List<List<long>> lwss = new List<List<long>>();
            
            for (long gy = 8; gy < (h - 8); gy += 18) {
                for (long gx = 8; gx < (w - 8); gx += 22) {
                    long kind = ((((gx * 7) + (gy * 11))) % 3);
                    if (kind == 0) {
                        long ph = (glider).Count;
                        for (long py = 0; py < ph; py += 1) {
                            long pw = (glider[(int)(py)]).Count;
                            for (long px = 0; px < pw; px += 1) {
                                if (glider[(int)(py)][(int)(px)] == 1) {
                                    grid[(int)((((gy + py)) % h))][(int)((((gx + px)) % w))] = 1;
                                }
                            }
                        }
                    } else {
                        if (kind == 1) {
                            long ph = (r_pentomino).Count;
                            for (long py = 0; py < ph; py += 1) {
                                long pw = (r_pentomino[(int)(py)]).Count;
                                for (long px = 0; px < pw; px += 1) {
                                    if (r_pentomino[(int)(py)][(int)(px)] == 1) {
                                        grid[(int)((((gy + py)) % h))][(int)((((gx + px)) % w))] = 1;
                                    }
                                }
                            }
                        } else {
                            long ph = (lwss).Count;
                            for (long py = 0; py < ph; py += 1) {
                                long pw = (lwss[(int)(py)]).Count;
                                for (long px = 0; px < pw; px += 1) {
                                    if (lwss[(int)(py)][(int)(px)] == 1) {
                                        grid[(int)((((gy + py)) % h))][(int)((((gx + px)) % w))] = 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
            List<List<byte>> frames = new List<unknown>();
            for (long _ = 0; _ < steps; _ += 1) {
                frames.Add(render(grid, w, h, cell));
                grid = next_state(grid, w, h);
            }
            save_gif(out_path, (w * cell), (h * cell), frames, grayscale_palette());
            unknown elapsed = (perf_counter() - start);
            Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
            Console.WriteLine(string.Join(" ", new object[] { "frames:", steps }));
            Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
        }
        
        public static void Main(string[] args)
        {
                run_07_game_of_life_loop();
        }
    }
    */
}
