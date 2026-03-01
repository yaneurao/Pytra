public final class Pytra_10_plasma_effect {
    private Pytra_10_plasma_effect() {
    }


    // 10: Sample that outputs a plasma effect as a GIF.

    public static void run_10_plasma_effect() {
        long w = 320L;
        long h = 240L;
        long frames_n = 216L;
        String out_path = "sample/out/10_plasma_effect.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long t = 0L; (__step_0 >= 0L) ? (t < frames_n) : (t > frames_n); t += __step_0) {
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
            long __step_1 = 1L;
            for (long y = 0L; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
                long row_base = y * w;
                long __step_2 = 1L;
                for (long x = 0L; (__step_2 >= 0L) ? (x < w) : (x > w); x += __step_2) {
                    long dx = x - 160L;
                    long dy = y - 120L;
                    double v = Math.sin((((double)(x)) + ((double)(t)) * 2.0) * 0.045) + Math.sin((((double)(y)) - ((double)(t)) * 1.2) * 0.05) + Math.sin((((double)(x + y)) + ((double)(t)) * 1.7) * 0.03) + Math.sin(Math.sqrt(dx * dx + dy * dy) * 0.07 - ((double)(t)) * 0.18);
                    long c = PyRuntime.__pytra_int((v + 4.0) * (255.0 / 8.0));
                    if ((c < 0L)) {
                        c = 0L;
                    }
                    if ((c > 255L)) {
                        c = 255L;
                    }
                    frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), c);
                }
            }
            frames.add(new java.util.ArrayList<Long>(frame));
        }
        PyRuntime.__pytra_noop(out_path, w, h, frames, new java.util.ArrayList<Long>());
        double elapsed = (System.nanoTime() / 1000000000.0) - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_10_plasma_effect();
    }
}
