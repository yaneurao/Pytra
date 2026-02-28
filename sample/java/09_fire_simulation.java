// Auto-generated Java native source from EAST3.
public final class Pytra_09_fire_simulation {
    private Pytra_09_fire_simulation() {
    }


    public static java.util.ArrayList<Long> fire_palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < 256L) : (i > 256L); i += __step_0) {
            long r = 0L;
            long g = 0L;
            long b = 0L;
            if ((i < 85L)) {
                r = (i * 3L);
                g = 0L;
                b = 0L;
            } else {
                if ((i < 170L)) {
                    r = 255L;
                    g = ((i - 85L) * 3L);
                    b = 0L;
                } else {
                    r = 255L;
                    g = 255L;
                    b = ((i - 170L) * 3L);
                }
            }
            p.add(r);
            p.add(g);
            p.add(b);
        }
        return new java.util.ArrayList<Long>(p);
    }

    public static void run_09_fire_simulation() {
        long w = 380L;
        long h = 260L;
        long steps = 420L;
        String out_path = "sample/out/09_fire_simulation.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> heat = new java.util.ArrayList<Object>();
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < h) : (__ > h); __ += __step_0) {
            heat.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_1 = 1L;
        for (long t = 0L; (__step_1 >= 0L) ? (t < steps) : (t > steps); t += __step_1) {
            long __step_2 = 1L;
            for (long x = 0L; (__step_2 >= 0L) ? (x < w) : (x > w); x += __step_2) {
                long val = (170L + (((x * 13L) + (t * 17L)) % 86L));
                ((java.util.ArrayList<Object>)(heat.get((int)(((((h - 1L)) < 0L) ? (((long)(heat.size())) + ((h - 1L))) : ((h - 1L))))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)(((((h - 1L)) < 0L) ? (((long)(heat.size())) + ((h - 1L))) : ((h - 1L))))))).size())) + (x)) : (x))), val);
            }
            long __step_3 = 1L;
            for (long y = 1L; (__step_3 >= 0L) ? (y < h) : (y > h); y += __step_3) {
                long __step_4 = 1L;
                for (long x = 0L; (__step_4 >= 0L) ? (x < w) : (x > w); x += __step_4) {
                    long a = ((Long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + (x)) : (x))))));
                    long b = ((Long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)(((((((x - 1L) + w) % w)) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + ((((x - 1L) + w) % w))) : ((((x - 1L) + w) % w)))))));
                    long c = ((Long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)((((((x + 1L) % w)) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + (((x + 1L) % w))) : (((x + 1L) % w)))))));
                    long d = ((Long)(((java.util.ArrayList<Object>)(heat.get((int)((((((y + 1L) % h)) < 0L) ? (((long)(heat.size())) + (((y + 1L) % h))) : (((y + 1L) % h))))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)((((((y + 1L) % h)) < 0L) ? (((long)(heat.size())) + (((y + 1L) % h))) : (((y + 1L) % h))))))).size())) + (x)) : (x))))));
                    long v = ((((a + b) + c) + d) / 4L);
                    long cool = (1L + (((x + y) + t) % 3L));
                    long nv = (v - cool);
                    ((java.util.ArrayList<Object>)(heat.get((int)(((((y - 1L)) < 0L) ? (((long)(heat.size())) + ((y - 1L))) : ((y - 1L))))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)(((((y - 1L)) < 0L) ? (((long)(heat.size())) + ((y - 1L))) : ((y - 1L))))))).size())) + (x)) : (x))), (((nv > 0L)) ? (nv) : (0L)));
                }
            }
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray((w * h));
            long __step_5 = 1L;
            for (long yy = 0L; (__step_5 >= 0L) ? (yy < h) : (yy > h); yy += __step_5) {
                long row_base = (yy * w);
                long __step_6 = 1L;
                for (long xx = 0L; (__step_6 >= 0L) ? (xx < w) : (xx > w); xx += __step_6) {
                    frame.set((int)(((((row_base + xx)) < 0L) ? (((long)(frame.size())) + ((row_base + xx))) : ((row_base + xx)))), ((Long)(((java.util.ArrayList<Object>)(heat.get((int)((((yy) < 0L) ? (((long)(heat.size())) + (yy)) : (yy)))))).get((int)((((xx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(heat.get((int)((((yy) < 0L) ? (((long)(heat.size())) + (yy)) : (yy)))))).size())) + (xx)) : (xx)))))));
                }
            }
            frames.add(new java.util.ArrayList<Long>(frame));
        }
        PyRuntime.__pytra_noop(out_path, w, h, frames, fire_palette());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(steps));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_09_fire_simulation();
    }
}
