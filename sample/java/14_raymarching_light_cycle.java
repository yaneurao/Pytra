public final class Pytra_14_raymarching_light_cycle {
    private Pytra_14_raymarching_light_cycle() {
    }


    // 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

    public static java.util.ArrayList<Long> palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < 256L) : (i > 256L); i += __step_0) {
            long r = Math.min(255L, PyRuntime.__pytra_int((((double)(20L)) + (((double)(i)) * 0.9))));
            long g = Math.min(255L, PyRuntime.__pytra_int((((double)(10L)) + (((double)(i)) * 0.7))));
            long b = Math.min(255L, (30L + i));
            p.add(r);
            p.add(g);
            p.add(b);
        }
        return new java.util.ArrayList<Long>(p);
    }

    public static long scene(double x, double y, double light_x, double light_y) {
        double x1 = (x + 0.45);
        double y1 = (y + 0.2);
        double x2 = (x - 0.35);
        double y2 = (y - 0.15);
        double r1 = Math.sqrt(((x1 * x1) + (y1 * y1)));
        double r2 = Math.sqrt(((x2 * x2) + (y2 * y2)));
        double blob = (Math.exp((((-7.0) * r1) * r1)) + Math.exp((((-8.0) * r2) * r2)));
        double lx = (x - light_x);
        double ly = (y - light_y);
        double l = Math.sqrt(((lx * lx) + (ly * ly)));
        double lit = (1.0 / (1.0 + ((3.5 * l) * l)));
        long v = PyRuntime.__pytra_int((((255.0 * blob) * lit) * 5.0));
        return Math.min(255L, Math.max(0L, v));
    }

    public static void run_14_raymarching_light_cycle() {
        long w = 320L;
        long h = 240L;
        long frames_n = 84L;
        String out_path = "sample/out/14_raymarching_light_cycle.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        double __hoisted_cast_1 = ((double)(frames_n));
        double __hoisted_cast_2 = ((double)((h - 1L)));
        double __hoisted_cast_3 = ((double)((w - 1L)));
        long __step_0 = 1L;
        for (long t = 0L; (__step_0 >= 0L) ? (t < frames_n) : (t > frames_n); t += __step_0) {
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray((w * h));
            double a = (((((double)(t)) / __hoisted_cast_1) * Math.PI) * 2.0);
            double light_x = (0.75 * Math.cos(a));
            double light_y = (0.55 * Math.sin((a * 1.2)));
            long __step_1 = 1L;
            for (long y = 0L; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
                long row_base = (y * w);
                double py = (((((double)(y)) / __hoisted_cast_2) * 2.0) - 1.0);
                long __step_2 = 1L;
                for (long x = 0L; (__step_2 >= 0L) ? (x < w) : (x > w); x += __step_2) {
                    double px = (((((double)(x)) / __hoisted_cast_3) * 2.0) - 1.0);
                    frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), scene(px, py, light_x, light_y));
                }
            }
            frames.add(new java.util.ArrayList<Long>(frame));
        }
        PyRuntime.__pytra_noop(out_path, w, h, frames, palette());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_14_raymarching_light_cycle();
    }
}
