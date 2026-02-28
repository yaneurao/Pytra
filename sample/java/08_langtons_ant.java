public final class Pytra_08_langtons_ant {
    private Pytra_08_langtons_ant() {
    }


    // 08: Sample that outputs Langton's Ant trajectories as a GIF.

    public static java.util.ArrayList<Long> capture(java.util.ArrayList<Object> grid, long w, long h) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray((w * h));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < h) : (y > h); y += __step_0) {
            long row_base = (y * w);
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < w) : (x > w); x += __step_1) {
                frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), (((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) != 0L)) ? (255L) : (0L)));
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_08_langtons_ant() {
        long w = 420L;
        long h = 420L;
        String out_path = "sample/out/08_langtons_ant.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> grid = new java.util.ArrayList<Object>();
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < h) : (__ > h); __ += __step_0) {
            grid.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        long x = (w / 2L);
        long y = (h / 2L);
        long d = 0L;
        long steps_total = 600000L;
        long capture_every = 3000L;
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_1 = 1L;
        for (long i = 0L; (__step_1 >= 0L) ? (i < steps_total) : (i > steps_total); i += __step_1) {
            if ((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) == 0L)) {
                d = ((d + 1L) % 4L);
                ((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 1L);
            } else {
                d = ((d + 3L) % 4L);
                ((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 0L);
            }
            if ((d == 0L)) {
                y = (((y - 1L) + h) % h);
            } else {
                if ((d == 1L)) {
                    x = ((x + 1L) % w);
                } else {
                    if ((d == 2L)) {
                        y = ((y + 1L) % h);
                    } else {
                        x = (((x - 1L) + w) % w);
                    }
                }
            }
            if (((i % capture_every) == 0L)) {
                frames.add(capture(grid, w, h));
            }
        }
        PyRuntime.__pytra_noop(out_path, w, h, frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_08_langtons_ant();
    }
}
