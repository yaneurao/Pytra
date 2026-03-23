final class _12_sort_visualizer {
    private _12_sort_visualizer() {
    }


    // 12: Sample that outputs intermediate states of bubble sort as a GIF.

    public static java.util.ArrayList<Long> render(java.util.ArrayList<Long> values, long w, long h) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
        long n = ((long)(values.size()));
        double bar_w = ((double)(w)) / ((double)(n));
        for (long i = 0L; i < n; i += 1L) {
            long x0 = PyRuntime.__pytra_int(((double)(i)) * bar_w);
            long x1 = PyRuntime.__pytra_int((((double)(i + 1L))) * bar_w);
            if (((x1) <= (x0))) {
                x1 = x0 + 1L;
            }
            long bh = PyRuntime.__pytra_int(((double)(((Long)(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))))))) / ((double)(n)) * ((double)(h)));
            long y = h - bh;
            for (y = y; y < h; y += 1L) {
                for (long x = x0; x < x1; x += 1L) {
                    frame.set((int)((((y * w + x) < 0L) ? (((long)(frame.size())) + (y * w + x)) : (y * w + x))), 255L);
                }
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_12_sort_visualizer() {
        long w = 320L;
        long h = 180L;
        long n = 124L;
        String out_path = "sample/out/12_sort_visualizer.gif";
        double start = time.perf_counter();
        java.util.ArrayList<Long> values = new java.util.ArrayList<Long>();
        long i = 0L;
        for (i = 0L; i < n; i += 1L) {
            values.add((i * 37L + 19L) % n);
        }
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>(java.util.Arrays.asList(render(values, w, h)));
        long frame_stride = 16L;
        long op = 0L;
        for (i = 0L; i < n; i += 1L) {
            boolean swapped = false;
            for (long j = 0L; j < n - i - 1L; j += 1L) {
                if (((((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))))))) > (((Long)(values.get((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L))))))))) {
                    long __swap_tmp_0 = ((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))))));
                    values.set((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))), ((Long)(values.get((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L)))))));
                    values.set((int)((((j + 1L) < 0L) ? (((long)(values.size())) + (j + 1L)) : (j + 1L))), __swap_tmp_0);
                    swapped = true;
                }
                if (((op % frame_stride) == (0L))) {
                    frames.add(render(values, w, h));
                }
                op += 1L;
            }
            if ((!swapped)) {
                break;
            }
        }
        gif.save_gif(out_path, w, h, frames, gif.grayscale_palette(), 3L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_12_sort_visualizer();
    }
}
