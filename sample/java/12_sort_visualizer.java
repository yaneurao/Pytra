// Auto-generated Java native source from EAST3.
public final class Pytra_12_sort_visualizer {
    private Pytra_12_sort_visualizer() {
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

    public static java.util.ArrayList<Long> render(java.util.ArrayList<Object> values, long w, long h) {
        java.util.ArrayList<Long> frame = __pytra_bytearray((w * h));
        long n = ((long)(values.size()));
        double bar_w = (((double)(w)) / ((double)(n)));
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < n) : (i > n); i += __step_0) {
            long x0 = __pytra_int((((double)(i)) * bar_w));
            long x1 = __pytra_int((((double)((i + 1L))) * bar_w));
            if ((x1 <= x0)) {
                x1 = (x0 + 1L);
            }
            long bh = __pytra_int(((((double)(((Long)(values.get((int)((((i) < 0L) ? (((long)(values.size())) + (i)) : (i)))))))) / ((double)(n))) * ((double)(h))));
            long y = (h - bh);
            long __step_1 = 1L;
            for (y = y; (__step_1 >= 0L) ? (y < h) : (y > h); y += __step_1) {
                long __step_2 = 1L;
                for (long x = x0; (__step_2 >= 0L) ? (x < x1) : (x > x1); x += __step_2) {
                    frame.set((int)((((((y * w) + x)) < 0L) ? (((long)(frame.size())) + (((y * w) + x))) : (((y * w) + x)))), 255L);
                }
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_12_sort_visualizer() {
        long w = 320L;
        long h = 180L;
        long n = 124L;
        String out_path = "sample/out/12_sort_visualizer.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> values = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < n) : (i > n); i += __step_0) {
            values.add((((i * 37L) + 19L) % n));
        }
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList(render(values, w, h)));
        long frame_stride = 16L;
        long op = 0L;
        long __step_1 = 1L;
        for (long i = 0L; (__step_1 >= 0L) ? (i < n) : (i > n); i += __step_1) {
            boolean swapped = false;
            long __step_2 = 1L;
            for (long j = 0L; (__step_2 >= 0L) ? (j < ((n - i) - 1L)) : (j > ((n - i) - 1L)); j += __step_2) {
                if ((((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j)))))) > ((Long)(values.get((int)(((((j + 1L)) < 0L) ? (((long)(values.size())) + ((j + 1L))) : ((j + 1L))))))))) {
                    java.util.ArrayList<Object> __tuple_3 = ((java.util.ArrayList<Object>)(new java.util.ArrayList<Object>(java.util.Arrays.asList(((Long)(values.get((int)(((((j + 1L)) < 0L) ? (((long)(values.size())) + ((j + 1L))) : ((j + 1L))))))), ((Long)(values.get((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))))))))));
                    values.set((int)((((j) < 0L) ? (((long)(values.size())) + (j)) : (j))), ((Long)(__tuple_3.get(0))));
                    values.set((int)(((((j + 1L)) < 0L) ? (((long)(values.size())) + ((j + 1L))) : ((j + 1L)))), ((Long)(__tuple_3.get(1))));
                    swapped = true;
                }
                if (((op % frame_stride) == 0L)) {
                    frames.add(render(values, w, h));
                }
                op += 1L;
            }
            if ((!swapped)) {
                break;
            }
        }
        __pytra_noop(out_path, w, h, frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(((long)(frames.size()))));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_12_sort_visualizer();
    }
}
