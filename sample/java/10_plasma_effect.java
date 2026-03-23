final class _10_plasma_effect {
    private _10_plasma_effect() {
    }


    // 10: Sample that outputs a plasma effect as a GIF.

    public static void run_10_plasma_effect() {
        long w = 320L;
        long h = 240L;
        long frames_n = 216L;
        String out_path = "sample/out/10_plasma_effect.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long t = 0L; t < frames_n; t += 1L) {
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
            for (long y = 0L; y < h; y += 1L) {
                long row_base = y * w;
                for (long x = 0L; x < w; x += 1L) {
                    long dx = x - 160L;
                    long dy = y - 120L;
                    double v = math.sin((((double)(x)) + ((double)(t)) * 2.0) * 0.045) + math.sin((((double)(y)) - ((double)(t)) * 1.2) * 0.05) + math.sin((((double)(x + y)) + ((double)(t)) * 1.7) * 0.03) + math.sin(math.sqrt(dx * dx + dy * dy) * 0.07 - ((double)(t)) * 0.18);
                    long c = PyRuntime.__pytra_int((v + 4.0) * (255.0 / 8.0));
                    if (((c) < (0L))) {
                        c = 0L;
                    }
                    if (((c) > (255L))) {
                        c = 255L;
                    }
                    frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), c);
                }
            }
            frames.add(PyRuntime.__pytra_bytearray(frame));
        }
        gif.save_gif(out_path, w, h, frames, gif.grayscale_palette(), 3L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_10_plasma_effect();
    }
}
