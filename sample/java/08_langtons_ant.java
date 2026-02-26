// Auto-generated Java native source from EAST3.
public final class Pytra_08_langtons_ant {
    private Pytra_08_langtons_ant() {
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

    public static java.util.ArrayList<Long> capture(java.util.ArrayList<Object> grid, long w, long h) {
        java.util.ArrayList<Long> frame = __pytra_bytearray((w * h));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < h) : (y > h); y += __step_0) {
            long row_base = (y * w);
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < w) : (x > w); x += __step_1) {
                frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), (((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) != 0L)) ? (255L) : (0L)));
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_08_langtons_ant() {
        long w = 420L;
        long h = 420L;
        String out_path = "sample/out/08_langtons_ant.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> grid = new java.util.ArrayList<Object>();
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < h) : (__ > h); __ += __step_0) {
            grid.add(__pytra_list_repeat(0L, w));
        }
        long x = (w / 2L);
        long y = (h / 2L);
        long d = 0L;
        long steps_total = 600000L;
        long capture_every = 3000L;
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_1 = 1L;
        for (long i = 0L; (__step_1 >= 0L) ? (i < steps_total) : (i > steps_total); i += __step_1) {
            if ((((Long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).get((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x)))))) == 0L)) {
                d = ((d + 1L) % 4L);
                ((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 1L);
            } else {
                d = ((d + 3L) % 4L);
                ((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).set((int)((((x) < 0L) ? (((long)(((java.util.ArrayList<Object>)(grid.get((int)((((y) < 0L) ? (((long)(grid.size())) + (y)) : (y)))))).size())) + (x)) : (x))), 0L);
            }
            if ((d == 0L)) {
                y = (((y - 1L) + h) % h);
            } else {
                if ((d == 1L)) {
                    x = ((x + 1L) % w);
                } else {
                    if ((d == 2L)) {
                        y = ((y + 1L) % h);
                    } else {
                        x = (((x - 1L) + w) % w);
                    }
                }
            }
            if (((i % capture_every) == 0L)) {
                frames.add(capture(grid, w, h));
            }
        }
        __pytra_noop(out_path, w, h, frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_08_langtons_ant();
    }
}
