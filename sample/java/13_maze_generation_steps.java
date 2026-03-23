final class _13_maze_generation_steps {
    private _13_maze_generation_steps() {
    }


    // 13: Sample that outputs DFS maze-generation progress as a GIF.

    public static java.util.ArrayList<Long> capture(java.util.ArrayList<java.util.ArrayList<Long>> grid, long w, long h, long scale) {
        long width = w * scale;
        long height = h * scale;
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(width * height);
        for (long y = 0L; y < h; y += 1L) {
            for (long x = 0L; x < w; x += 1L) {
                long v = ((((((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))))))) == (0L))) ? (255L) : (40L));
                for (long yy = 0L; yy < scale; yy += 1L) {
                    long base = (y * scale + yy) * width + x * scale;
                    for (long xx = 0L; xx < scale; xx += 1L) {
                        frame.set((int)((((base + xx) < 0L) ? (((long)(frame.size())) + (base + xx)) : (base + xx))), v);
                    }
                }
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_13_maze_generation_steps() {
        long cell_w = 89L;
        long cell_h = 67L;
        long scale = 5L;
        long capture_every = 20L;
        String out_path = "sample/out/13_maze_generation_steps.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> grid = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long __ = 0L; __ < cell_h; __ += 1L) {
            grid.add(PyRuntime.__pytra_list_repeat(1L, cell_w));
        }
        java.util.ArrayList<java.util.ArrayList<Object>> stack = new java.util.ArrayList<java.util.ArrayList<Object>>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 1L))));
        ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((1L) < 0L) ? (((long)(grid.size())) + (1L)) : (1L)))))).set((int)((((1L) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((1L) < 0L) ? (((long)(grid.size())) + (1L)) : (1L)))))).size())) + (1L)) : (1L))), 0L);
        java.util.ArrayList<java.util.ArrayList<Object>> dirs = new java.util.ArrayList<java.util.ArrayList<Object>>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(2L, 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList((-(2L)), 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 2L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, (-(2L))))));
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        long step = 0L;
        while (((stack) != null && !(stack).isEmpty())) {
            java.util.ArrayList<Object> __tuple_0 = ((java.util.ArrayList<Object>)(Object)(stack.get((int)(((((-(1L))) < 0L) ? (((long)(stack.size())) + ((-(1L)))) : ((-(1L))))))));
            long x = ((Long)(__tuple_0.get(0)));
            long y = ((Long)(__tuple_0.get(1)));
            java.util.ArrayList<java.util.ArrayList<Object>> candidates = new java.util.ArrayList<java.util.ArrayList<Object>>();
            long nx = 0L;
            long ny = 0L;
            for (long k = 0L; k < 4L; k += 1L) {
                java.util.ArrayList<Object> __tuple_1 = ((java.util.ArrayList<Object>)(Object)(dirs.get((int)((((k) < 0L) ? (((long)(dirs.size())) + (k)) : (k))))));
                long dx = ((Long)(__tuple_1.get(0)));
                long dy = ((Long)(__tuple_1.get(1)));
                nx = x + dx;
                ny = y + dy;
                if ((((nx) >= (1L)) && ((nx) < (cell_w - 1L)) && ((ny) >= (1L)) && ((ny) < (cell_h - 1L)) && ((((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).get((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx))))))) == (1L)))) {
                    if (((dx) == (2L))) {
                        candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x + 1L, y)));
                    } else {
                        if (((dx) == ((-(2L))))) {
                            candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x - 1L, y)));
                        } else {
                            if (((dy) == (2L))) {
                                candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x, y + 1L)));
                            } else {
                                candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x, y - 1L)));
                            }
                        }
                    }
                }
            }
            if (((((long)(candidates.size()))) == (0L))) {
                stack.remove(stack.size() - 1);
            } else {
                Object sel = candidates.get((int)(((((x * 17L + y * 29L + ((long)(stack.size())) * 13L) % ((long)(candidates.size()))) < 0L) ? (((long)(candidates.size())) + ((x * 17L + y * 29L + ((long)(stack.size())) * 13L) % ((long)(candidates.size())))) : ((x * 17L + y * 29L + ((long)(stack.size())) * 13L) % ((long)(candidates.size()))))));
                java.util.ArrayList<Object> __tuple_2 = ((java.util.ArrayList<Object>)(Object)(sel));
                nx = ((Long)(__tuple_2.get(0)));
                ny = ((Long)(__tuple_2.get(1)));
                long wx = ((Long)(__tuple_2.get(2)));
                long wy = ((Long)(__tuple_2.get(3)));
                ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((wy) < 0L) ? (((long)(grid.size())) + (wy)) : (wy)))))).set((int)((((wx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((wy) < 0L) ? (((long)(grid.size())) + (wy)) : (wy)))))).size())) + (wx)) : (wx))), 0L);
                ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).set((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx))), 0L);
                stack.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny)));
            }
            if (((step % capture_every) == (0L))) {
                frames.add(capture(grid, cell_w, cell_h, scale));
            }
            step += 1L;
        }
        frames.add(capture(grid, cell_w, cell_h, scale));
        gif.save_gif(out_path, cell_w * scale, cell_h * scale, frames, gif.grayscale_palette(), 4L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_13_maze_generation_steps();
    }
}
