final class _09_fire_simulation {
    private _09_fire_simulation() {
    }


    // 09: Sample that outputs a simple fire effect as a GIF.

    public static java.util.ArrayList<Long> fire_palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        for (long i = 0L; i < 256L; i += 1L) {
            long r = 0L;
            long g = 0L;
            long b = 0L;
            if (((i) < (85L))) {
                r = i * 3L;
                g = 0L;
                b = 0L;
            } else {
                if (((i) < (170L))) {
                    r = 255L;
                    g = (i - 85L) * 3L;
                    b = 0L;
                } else {
                    r = 255L;
                    g = 255L;
                    b = (i - 170L) * 3L;
                }
            }
            p.add(r);
            p.add(g);
            p.add(b);
        }
        return PyRuntime.__pytra_bytearray(p);
    }

    public static void run_09_fire_simulation() {
        long w = 380L;
        long h = 260L;
        long steps = 420L;
        String out_path = "sample/out/09_fire_simulation.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> heat = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long __ = 0L; __ < h; __ += 1L) {
            heat.add(PyRuntime.__pytra_list_repeat(0L, w));
        }
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long t = 0L; t < steps; t += 1L) {
            long x = 0L;
            for (x = 0L; x < w; x += 1L) {
                long val = 170L + (x * 13L + t * 17L) % 86L;
                ((java.util.ArrayList<Object>)(Object)(heat.get((int)((((h - 1L) < 0L) ? (((long)(heat.size())) + (h - 1L)) : (h - 1L)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((h - 1L) < 0L) ? (((long)(heat.size())) + (h - 1L)) : (h - 1L)))))).size())) + (x)) : (x))), val);
            }
            for (long y = 1L; y < h; y += 1L) {
                for (x = 0L; x < w; x += 1L) {
                    long a = ((Long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + (x)) : (x))))));
                    long b = ((Long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)(((((x - 1L + w) % w) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + ((x - 1L + w) % w)) : ((x - 1L + w) % w))))));
                    long c = ((Long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).get((int)(((((x + 1L) % w) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y) < 0L) ? (((long)(heat.size())) + (y)) : (y)))))).size())) + ((x + 1L) % w)) : ((x + 1L) % w))))));
                    long d = ((Long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)(((((y + 1L) % h) < 0L) ? (((long)(heat.size())) + ((y + 1L) % h)) : ((y + 1L) % h)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)(((((y + 1L) % h) < 0L) ? (((long)(heat.size())) + ((y + 1L) % h)) : ((y + 1L) % h)))))).size())) + (x)) : (x))))));
                    long v = (a + b + c + d) / 4L;
                    long cool = 1L + (x + y + t) % 3L;
                    long nv = v - cool;
                    ((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y - 1L) < 0L) ? (((long)(heat.size())) + (y - 1L)) : (y - 1L)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((y - 1L) < 0L) ? (((long)(heat.size())) + (y - 1L)) : (y - 1L)))))).size())) + (x)) : (x))), ((((nv) > (0L))) ? (nv) : (0L)));
                }
            }
            java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(w * h);
            for (long yy = 0L; yy < h; yy += 1L) {
                long row_base = yy * w;
                for (long xx = 0L; xx < w; xx += 1L) {
                    frame.set((int)((((row_base + xx) < 0L) ? (((long)(frame.size())) + (row_base + xx)) : (row_base + xx))), ((Long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((yy) < 0L) ? (((long)(heat.size())) + (yy)) : (yy)))))).get((int)((((xx) < 0L) ? (((long)(((java.util.ArrayList<Object>)(Object)(heat.get((int)((((yy) < 0L) ? (((long)(heat.size())) + (yy)) : (yy)))))).size())) + (xx)) : (xx)))))));
                }
            }
            frames.add(PyRuntime.__pytra_bytearray(frame));
        }
        gif.save_gif(out_path, w, h, frames, fire_palette(), 4L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(steps));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_09_fire_simulation();
    }
}
