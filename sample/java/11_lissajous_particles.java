final class _11_lissajous_particles {
    private _11_lissajous_particles() {
    }


    // 11: Sample that outputs Lissajous-motion particles as a GIF.

    public static java.util.ArrayList<Long> color_palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        for (long i = 0L; i < 256L; i += 1L) {
            long r = i;
            long g = i * 3L % 256L;
            long b = 255L - i;
            p.add(r);
            p.add(g);
            p.add(b);
        }
        return PyRuntime.__pytra_bytearray(p);
    }

    public static void run_11_lissajous_particles() {
        long w = 320L;
        long h = 240L;
        long frames_n = 360L;
        long particles = 48L;
        String out_path = "sample/out/11_lissajous_particles.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long t = 0L; t < frames_n; t += 1L) {
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
            for (long p = 0L; p < particles; p += 1L) {
                double phase = ((double)(p)) * 0.261799;
                long x = PyRuntime.__pytra_int(((double)(w)) * 0.5 + ((double)(w)) * 0.38 * math.sin(0.11 * ((double)(t)) + phase * 2.0));
                long y = PyRuntime.__pytra_int(((double)(h)) * 0.5 + ((double)(h)) * 0.38 * math.sin(0.17 * ((double)(t)) + phase * 3.0));
                long color = 30L + p * 9L % 220L;
                for (long dy = (-(2L)); dy < 3L; dy += 1L) {
                    for (long dx = (-(2L)); dx < 3L; dx += 1L) {
                        long xx = x + dx;
                        long yy = y + dy;
                        if ((((xx) >= (0L)) && ((xx) < (w)) && ((yy) >= (0L)) && ((yy) < (h)))) {
                            long d2 = dx * dx + dy * dy;
                            if (((d2) <= (4L))) {
                                long idx = yy * w + xx;
                                long v = color - d2 * 20L;
                                v = Math.max(0L, v);
                                if (((v) > (((Long)(frame.get((int)((((idx) < 0L) ? (((long)(frame.size())) + (idx)) : (idx))))))))) {
                                    frame.set((int)((((idx) < 0L) ? (((long)(frame.size())) + (idx)) : (idx))), v);
                                }
                            }
                        }
                    }
                }
            }
            frames.add(PyRuntime.__pytra_bytearray(frame));
        }
        gif.save_gif(out_path, w, h, frames, color_palette(), 3L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_11_lissajous_particles();
    }
}
