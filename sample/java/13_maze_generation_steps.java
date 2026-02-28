// Auto-generated Java native source from EAST3.
public final class Pytra_13_maze_generation_steps {
    private Pytra_13_maze_generation_steps() {
    }


    public static java.util.ArrayList<Long> capture(java.util.ArrayList<Object> grid, long w, long h, long scale) {
        long width = (w * scale);
        long height = (h * scale);
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray((width * height));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < h) : (y > h); y += __step_0) {
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < w) : (x > w); x += __step_1) {
                long v = (((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) == 0L)) ? (255L) : (40L));
                long __step_2 = 1L;
                for (long yy = 0L; (__step_2 >= 0L) ? (yy < scale) : (yy > scale); yy += __step_2) {
                    long base = ((((y * scale) + yy) * width) + (x * scale));
                    long __step_3 = 1L;
                    for (long xx = 0L; (__step_3 >= 0L) ? (xx < scale) : (xx > scale); xx += __step_3) {
                        frame.set((int)(((((base + xx)) < 0L) ? (((long)(frame.size())) + ((base + xx))) : ((base + xx)))), v);
                    }
                }
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_13_maze_generation_steps() {
        long cell_w = 89L;
        long cell_h = 67L;
        long scale = 5L;
        long capture_every = 20L;
        String out_path = "sample/out/13_maze_generation_steps.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> grid = new java.util.ArrayList<Object>();
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < cell_h) : (__ > cell_h); __ += __step_0) {
            grid.add(PyRuntime.__pytra_list_repeat(1L, cell_w));
        }
        java.util.ArrayList<Object> stack = new java.util.ArrayList<Object>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(1L, 1L))));
        ((java.util.ArrayList<Object>)(grid.get((int)((((1L) < 0L) ? (((long)(grid.size())) + (1L)) : (1L)))))).set((int)((((1L) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((1L) < 0L) ? (((long)(grid.size())) + (1L)) : (1L)))))).size())) + (1L)) : (1L))), 0L);
        java.util.ArrayList<Object> dirs = new java.util.ArrayList<Object>(java.util.Arrays.asList(new java.util.ArrayList<Object>(java.util.Arrays.asList(2L, 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList((-2L), 0L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 2L)), new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, (-2L)))));
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long step = 0L;
        while (((stack) != null && !(stack).isEmpty())) {
            java.util.ArrayList<Object> __tuple_1 = ((java.util.ArrayList<Object>)(stack.get((int)(((((-1L)) < 0L) ? (((long)(stack.size())) + ((-1L))) : ((-1L)))))));
            long x = ((Long)(__tuple_1.get(0)));
            long y = ((Long)(__tuple_1.get(1)));
            java.util.ArrayList<Object> candidates = new java.util.ArrayList<Object>(java.util.Arrays.asList());
            long __step_2 = 1L;
            for (long k = 0L; (__step_2 >= 0L) ? (k < 4L) : (k > 4L); k += __step_2) {
                java.util.ArrayList<Object> __tuple_3 = ((java.util.ArrayList<Object>)(dirs.get((int)((((k) < 0L) ? (((long)(dirs.size())) + (k)) : (k))))));
                long dx = ((Long)(__tuple_3.get(0)));
                long dy = ((Long)(__tuple_3.get(1)));
                long nx = (x + dx);
                long ny = (y + dy);
                if (((nx >= 1L) && (nx < (cell_w - 1L)) && (ny >= 1L) && (ny < (cell_h - 1L)) && (((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).get((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx)))))) == 1L))) {
                    if ((dx == 2L)) {
                        candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, (x + 1L), y)));
                    } else {
                        if ((dx == (-2L))) {
                            candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, (x - 1L), y)));
                        } else {
                            if ((dy == 2L)) {
                                candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x, (y + 1L))));
                            } else {
                                candidates.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny, x, (y - 1L))));
                            }
                        }
                    }
                }
            }
            if ((((long)(candidates.size())) == 0L)) {
                stack.remove(stack.size() - 1);
            } else {
                Object sel = candidates.get((int)((((((((x * 17L) + (y * 29L)) + (((long)(stack.size())) * 13L)) % ((long)(candidates.size())))) < 0L) ? (((long)(candidates.size())) + (((((x * 17L) + (y * 29L)) + (((long)(stack.size())) * 13L)) % ((long)(candidates.size()))))) : (((((x * 17L) + (y * 29L)) + (((long)(stack.size())) * 13L)) % ((long)(candidates.size())))))));
                java.util.ArrayList<Object> __tuple_4 = ((java.util.ArrayList<Object>)(sel));
                long nx = ((Long)(__tuple_4.get(0)));
                long ny = ((Long)(__tuple_4.get(1)));
                long wx = ((Long)(__tuple_4.get(2)));
                long wy = ((Long)(__tuple_4.get(3)));
                ((java.util.ArrayList<Object>)(grid.get((int)((((wy) < 0L) ? (((long)(grid.size())) + (wy)) : (wy)))))).set((int)((((wx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((wy) < 0L) ? (((long)(grid.size())) + (wy)) : (wy)))))).size())) + (wx)) : (wx))), 0L);
                ((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).set((int)((((nx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((ny) < 0L) ? (((long)(grid.size())) + (ny)) : (ny)))))).size())) + (nx)) : (nx))), 0L);
                stack.add(new java.util.ArrayList<Object>(java.util.Arrays.asList(nx, ny)));
            }
            if (((step % capture_every) == 0L)) {
                frames.add(capture(grid, cell_w, cell_h, scale));
            }
            step += 1L;
        }
        frames.add(capture(grid, cell_w, cell_h, scale));
        PyRuntime.__pytra_noop(out_path, (cell_w * scale), (cell_h * scale), frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_13_maze_generation_steps();
    }
}
