final class _08_langtons_ant {
    private _08_langtons_ant() {
    }


    // 08: Sample that outputs Langton's Ant trajectories as a GIF.

    public static java.util.ArrayList<Long> capture(java.util.ArrayList<java.util.ArrayList<Long>> grid, long w, long h) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
        for (long y = 0L; y < h; y += 1L) {
            long row_base = y * w;
            for (long x = 0L; x < w; x += 1L) {
                frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), (((((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) != 0L)) ? (255L) : (0L)));
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_08_langtons_ant() {
        long w = 420L;
        long h = 420L;
        String out_path = "sample/out/08_langtons_ant.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> grid = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long __ = 0L; __ < h; __ += 1L) {
            grid.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        long x = w / 2L;
        long y = h / 2L;
        long d = 0L;
        long steps_total = 600000L;
        long capture_every = 3000L;
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long i = 0L; i < steps_total; i += 1L) {
            if (((((Long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))))))) == (0L))) {
                d = (d + 1L) % 4L;
                ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 1L);
            } else {
                d = (d + 3L) % 4L;
                ((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 0L);
            }
            if (((d) == (0L))) {
                y = (y - 1L + h) % h;
            } else {
                if (((d) == (1L))) {
                    x = (x + 1L) % w;
                } else {
                    if (((d) == (2L))) {
                        y = (y + 1L) % h;
                    } else {
                        x = (x - 1L + w) % w;
                    }
                }
            }
            if (((i % capture_every) == (0L))) {
                frames.add(capture(grid, w, h));
            }
        }
        gif.save_gif(out_path, w, h, frames, gif.grayscale_palette(), 5L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_08_langtons_ant();
    }
}
