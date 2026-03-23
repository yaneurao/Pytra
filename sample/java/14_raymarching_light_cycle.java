final class _14_raymarching_light_cycle {
    private _14_raymarching_light_cycle() {
    }


    // 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

    public static java.util.ArrayList<Long> palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        for (long i = 0L; i < 256L; i += 1L) {
            long r = Math.min(255L, PyRuntime.__pytra_int(((double)(20L)) + ((double)(i)) * 0.9));
            long g = Math.min(255L, PyRuntime.__pytra_int(((double)(10L)) + ((double)(i)) * 0.7));
            long b = Math.min(255L, 30L + i);
            p.add(r);
            p.add(g);
            p.add(b);
        }
        return PyRuntime.__pytra_bytearray(p);
    }

    public static long scene(double x, double y, double light_x, double light_y) {
        double x1 = x + 0.45;
        double y1 = y + 0.2;
        double x2 = x - 0.35;
        double y2 = y - 0.15;
        double r1 = math.sqrt(x1 * x1 + y1 * y1);
        double r2 = math.sqrt(x2 * x2 + y2 * y2);
        double blob = math.exp((-(7.0)) * r1 * r1) + math.exp((-(8.0)) * r2 * r2);
        double lx = x - light_x;
        double ly = y - light_y;
        double l = math.sqrt(lx * lx + ly * ly);
        double lit = 1.0 / (1.0 + 3.5 * l * l);
        long v = PyRuntime.__pytra_int(255.0 * blob * lit * 5.0);
        return Math.min(255L, Math.max(0L, v));
    }

    public static void run_14_raymarching_light_cycle() {
        long w = 320L;
        long h = 240L;
        long frames_n = 84L;
        String out_path = "sample/out/14_raymarching_light_cycle.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long t = 0L; t < frames_n; t += 1L) {
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
            double a = ((double)(t)) / ((double)(frames_n)) * math.pi * 2.0;
            double light_x = 0.75 * math.cos(a);
            double light_y = 0.55 * math.sin(a * 1.2);
            for (long y = 0L; y < h; y += 1L) {
                long row_base = y * w;
                double py = ((double)(y)) / (((double)(h - 1L))) * 2.0 - 1.0;
                for (long x = 0L; x < w; x += 1L) {
                    double px = ((double)(x)) / (((double)(w - 1L))) * 2.0 - 1.0;
                    frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), scene(px, py, light_x, light_y));
                }
            }
            frames.add(PyRuntime.__pytra_bytearray(frame));
        }
        gif.save_gif(out_path, w, h, frames, palette(), 3L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_14_raymarching_light_cycle();
    }
}
