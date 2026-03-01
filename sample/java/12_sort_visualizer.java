public final class Pytra_12_sort_visualizer {
    private Pytra_12_sort_visualizer() {
    }


    // 12: Sample that outputs intermediate states of bubble sort as a GIF.

    public static java.util.ArrayList<Long> render(java.util.ArrayList<Object> values, long w, long h) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
        long n = ((long)(values.size()));
        double bar_w = ((double)(w)) / ((double)(n));
        double __hoisted_cast_1 = ((double)(n));
        double __hoisted_cast_2 = ((double)(h));
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < n) : (i > n); i += __step_0) {
            long x0 = PyRuntime.__pytra_int(((double)(i)) * bar_w);
            long x1 = PyRuntime.__pytra_int((((double)(i + 1L))) * bar_w);
            if ((x1 <= x0)) {
                x1 = x0 + 1L;
            }
            long bh = PyRuntime.__pytra_int(((double)(((Long)(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))))))) / __hoisted_cast_1 * __hoisted_cast_2);
            long y = h - bh;
            long __step_1 = 1L;
            for (y = y; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
                long __step_2 = 1L;
                for (long x = x0; (__step_2 >= 0L) ? (x < x1) : (x > x1); x += __step_2) {
                    frame.set((int)((((y * w + x) < 0L) ? (((long)(frame.size())) + (y * w + x)) : (y * w + x))), 255L);
                }
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_12_sort_visualizer() {
        long w = 320L;
        long h = 180L;
        long n = 124L;
        String out_path = "sample/out/12_sort_visualizer.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> values = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < n) : (i > n); i += __step_0) {
            values.add((i * 37L + 19L) % n);
        }
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList(render(values, w, h)));
        long frame_stride = 16L;
        long op = 0L;
        long __step_1 = 1L;
        for (long i = 0L; (__step_1 >= 0L) ? (i < n) : (i > n); i += __step_1) {
            boolean swapped = false;
            long __step_2 = 1L;
            for (long j = 0L; (__step_2 >= 0L) ? (j < n - i - 1L) : (j > n - i - 1L); j += __step_2) {
                if ((((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j)))))) > ((Long)(values.get((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L)))))))) {
                    java.util.ArrayList<Object> __tuple_3 = ((java.util.ArrayList<Object>)(new java.util.ArrayList<Object>(java.util.Arrays.asList(((Long)(values.get((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L)))))), ((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))))))))));
                    values.set((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))), ((Long)(__tuple_3.get(0))));
                    values.set((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L))), ((Long)(__tuple_3.get(1))));
                    swapped = true;
                }
                if ((op % frame_stride == 0L)) {
                    frames.add(render(values, w, h));
                }
                op += 1L;
            }
            if ((!swapped)) {
                break;
            }
        }
        PyRuntime.__pytra_noop(out_path, w, h, frames, new java.util.ArrayList<Long>());
        double elapsed = (System.nanoTime() / 1000000000.0) - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_12_sort_visualizer();
    }
}
