// Auto-generated Java native source from EAST3.
public final class Pytra_09_fire_simulation {
    private Pytra_09_fire_simulation() {
    }

    private static void __pytra_noop(Object... args) {
    }

    private static long __pytra_int(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        if (value instanceof Boolean) {
            return ((Boolean) value) ? 1L : 0L;
        }
        if (value instanceof String) {
            String s = ((String) value).trim();
            if (s.isEmpty()) {
                return 0L;
            }
            try {
                return Long.parseLong(s);
            } catch (NumberFormatException ex) {
                return 0L;
            }
        }
        return 0L;
    }

    private static long __pytra_len(Object value) {
        if (value == null) {
            return 0L;
        }
        if (value instanceof String) {
            return ((String) value).length();
        }
        if (value instanceof java.util.Map<?, ?>) {
            return ((java.util.Map<?, ?>) value).size();
        }
        if (value instanceof java.util.List<?>) {
            return ((java.util.List<?>) value).size();
        }
        return 0L;
    }

    private static boolean __pytra_str_isdigit(Object value) {
        String s = String.valueOf(value);
        if (s.isEmpty()) {
            return false;
        }
        int i = 0;
        while (i < s.length()) {
            if (!Character.isDigit(s.charAt(i))) {
                return false;
            }
            i += 1;
        }
        return true;
    }

    private static boolean __pytra_str_isalpha(Object value) {
        String s = String.valueOf(value);
        if (s.isEmpty()) {
            return false;
        }
        int i = 0;
        while (i < s.length()) {
            if (!Character.isLetter(s.charAt(i))) {
                return false;
            }
            i += 1;
        }
        return true;
    }

    private static String __pytra_str_slice(String s, long start, long stop) {
        long n = s.length();
        long lo = start;
        long hi = stop;
        if (lo < 0L) {
            lo += n;
        }
        if (hi < 0L) {
            hi += n;
        }
        if (lo < 0L) {
            lo = 0L;
        }
        if (hi < 0L) {
            hi = 0L;
        }
        if (lo > n) {
            lo = n;
        }
        if (hi > n) {
            hi = n;
        }
        if (hi < lo) {
            hi = lo;
        }
        return s.substring((int) lo, (int) hi);
    }

    private static java.util.ArrayList<Long> __pytra_bytearray(Object init) {
        java.util.ArrayList<Long> out = new java.util.ArrayList<Long>();
        if (init instanceof Number) {
            long n = ((Number) init).longValue();
            long i = 0L;
            while (i < n) {
                out.add(0L);
                i += 1L;
            }
            return out;
        }
        if (init instanceof java.util.List<?>) {
            java.util.List<?> src = (java.util.List<?>) init;
            int i = 0;
            while (i < src.size()) {
                Object v = src.get(i);
                if (v instanceof Number) {
                    out.add(((Number) v).longValue());
                } else {
                    out.add(0L);
                }
                i += 1;
            }
        }
        return out;
    }

    private static java.util.HashMap<Object, Object> __pytra_dict_of(Object... kv) {
        java.util.HashMap<Object, Object> out = new java.util.HashMap<Object, Object>();
        int i = 0;
        while (i + 1 < kv.length) {
            out.put(kv[i], kv[i + 1]);
            i += 2;
        }
        return out;
    }

    private static java.util.ArrayList<Object> __pytra_list_repeat(Object value, long count) {
        java.util.ArrayList<Object> out = new java.util.ArrayList<Object>();
        long i = 0L;
        while (i < count) {
            out.add(value);
            i += 1L;
        }
        return out;
    }

    private static boolean __pytra_truthy(Object value) {
        if (value == null) {
            return false;
        }
        if (value instanceof Boolean) {
            return ((Boolean) value);
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue() != 0.0;
        }
        if (value instanceof String) {
            return !((String) value).isEmpty();
        }
        if (value instanceof java.util.List<?>) {
            return !((java.util.List<?>) value).isEmpty();
        }
        return true;
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
            heat.add(__pytra_list_repeat(0L, w));
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
            java.util.ArrayList<Long> frame = __pytra_bytearray((w * h));
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
        __pytra_noop(out_path, w, h, frames, fire_palette());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(steps));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_09_fire_simulation();
    }
}
