public static class Program
{
    // 13: Sample that outputs DFS maze-generation progress as a GIF.
    
    public static List<byte> capture(System.Collections.Generic.List<System.Collections.Generic.List<long>> grid, long w, long h, long scale)
    {
        long width = w * scale;
        long height = h * scale;
        List<byte> frame = bytearray(width * height);
        for (long y = 0; y < h; y += 1) {
            for (long x = 0; x < w; x += 1) {
                long v = (grid[System.Convert.ToInt32(y)][System.Convert.ToInt32(x)] == 0 ? 255 : 40);
                for (long yy = 0; yy < scale; yy += 1) {
                    long py_base = (y * scale + yy) * width + x * scale;
                    for (long xx = 0; xx < scale; xx += 1) {
                        frame[System.Convert.ToInt32(py_base + xx)] = v;
                    }
                }
            }
        }
        return bytes(frame);
    }
    
    public static void run_13_maze_generation_steps()
    {
        // Increase maze size and render resolution to ensure sufficient runtime.
        long cell_w = 89;
        long cell_h = 67;
        long scale = 5;
        long capture_every = 20;
        string out_path = "sample/out/13_maze_generation_steps.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<System.Collections.Generic.List<long>> grid = [[1] * cell_w for _ in range(cell_h)];
        System.Collections.Generic.List<(long, long)> stack = new System.Collections.Generic.List<(long, long)>();
        grid[System.Convert.ToInt32(1)][System.Convert.ToInt32(1)] = 0;
        
        System.Collections.Generic.List<(long, long)> dirs = new System.Collections.Generic.List<(long, long)>();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        long step = 0;
        
        while (stack.Count != 0) {
            var __tmp_1 = stack[System.Convert.ToInt32(-1)];
            x = __tmp_1.Item1;
            y = __tmp_1.Item2;
            System.Collections.Generic.List<(long, long, long, long)> candidates = new System.Collections.Generic.List<unknown>();
            for (long k = 0; k < 4; k += 1) {
                var __tmp_2 = dirs[System.Convert.ToInt32(k)];
                dx = __tmp_2.Item1;
                dy = __tmp_2.Item2;
                unknown nx = x + dx;
                unknown ny = y + dy;
                if (nx >= 1 && nx < cell_w - 1 && ny >= 1 && ny < cell_h - 1 && grid[System.Convert.ToInt32(ny)][System.Convert.ToInt32(nx)] == 1) {
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
                stack[stack.Count - 1];
            } else {
                (long, long, long, long) sel = candidates[System.Convert.ToInt32((x * 17 + y * 29 + (stack).Count * 13) % (candidates).Count)];
                (nx, ny, wx, wy) = sel;
                grid[System.Convert.ToInt32(wy)][System.Convert.ToInt32(wx)] = 0;
                grid[System.Convert.ToInt32(ny)][System.Convert.ToInt32(nx)] = 0;
                stack.Add((nx, ny));
            }
            if (step % capture_every == 0) {
                frames.Add(capture(grid, cell_w, cell_h, scale));
            }
            step += 1;
        }
        frames.Add(capture(grid, cell_w, cell_h, scale));
        save_gif(out_path, cell_w * scale, cell_h * scale, frames, grayscale_palette());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", (frames).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_13_maze_generation_steps();
    }
}
