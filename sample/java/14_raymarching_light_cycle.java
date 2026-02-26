// Auto-generated Java native source from EAST3.
public final class Pytra_14_raymarching_light_cycle {
    private Pytra_14_raymarching_light_cycle() {
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

    public static java.util.ArrayList<Long> palette() {
        java.util.ArrayList<Long> p = new java.util.ArrayList<Long>();
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < 256L) : (i > 256L); i += __step_0) {
            long r = Math.min(255L, __pytra_int((((double)(20L)) + (((double)(i)) * 0.9))));
            long g = Math.min(255L, __pytra_int((((double)(10L)) + (((double)(i)) * 0.7))));
            long b = Math.min(255L, __pytra_int((30L + i)));
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
        long v = __pytra_int((((255.0 * blob) * lit) * 5.0));
        return Math.min(255L, Math.max(0L, v));
    }

    public static void run_14_raymarching_light_cycle() {
        long w = 320L;
        long h = 240L;
        long frames_n = 84L;
        String out_path = "sample/out/14_raymarching_light_cycle.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long t = 0L; (__step_0 >= 0L) ? (t < frames_n) : (t > frames_n); t += __step_0) {
            java.util.ArrayList<Long> frame = __pytra_bytearray((w * h));
            double a = (((((double)(t)) / ((double)(frames_n))) * Math.PI) * 2.0);
            double light_x = (0.75 * Math.cos(a));
            double light_y = (0.55 * Math.sin((a * 1.2)));
            long __step_1 = 1L;
            for (long y = 0L; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
                long row_base = (y * w);
                double py = (((((double)(y)) / ((double)((h - 1L)))) * 2.0) - 1.0);
                long __step_2 = 1L;
                for (long x = 0L; (__step_2 >= 0L) ? (x < w) : (x > w); x += __step_2) {
                    double px = (((((double)(x)) / ((double)((w - 1L)))) * 2.0) - 1.0);
                    frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), scene(px, py, light_x, light_y));
                }
            }
            frames.add(new java.util.ArrayList<Long>(frame));
        }
        __pytra_noop(out_path, w, h, frames, palette());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_14_raymarching_light_cycle();
    }
}
