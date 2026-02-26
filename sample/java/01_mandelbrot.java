// Auto-generated Java native source from EAST3.
public final class Pytra_01_mandelbrot {
    private Pytra_01_mandelbrot() {
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

    public static long escape_count(double cx, double cy, long max_iter) {
        double x = 0.0;
        double y = 0.0;
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < max_iter) : (i > max_iter); i += __step_0) {
            double x2 = (x * x);
            double y2 = (y * y);
            if (((x2 + y2) > 4.0)) {
                return i;
            }
            y = (((2.0 * x) * y) + cy);
            x = ((x2 - y2) + cx);
        }
        return max_iter;
    }

    public static Object color_map(long iter_count, long max_iter) {
        if ((iter_count >= max_iter)) {
            return new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 0L, 0L));
        }
        double t = (((double)(iter_count)) / ((double)(max_iter)));
        long r = __pytra_int((255.0 * (t * t)));
        long g = __pytra_int((255.0 * t));
        long b = __pytra_int((255.0 * (1.0 - t)));
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(r, g, b));
    }

    public static java.util.ArrayList<Long> render_mandelbrot(long width, long height, long max_iter, double x_min, double x_max, double y_min, double y_max) {
        java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            double py = (y_min + ((y_max - y_min) * (((double)(y)) / ((double)((height - 1L))))));
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                double px = (x_min + ((x_max - x_min) * (((double)(x)) / ((double)((width - 1L))))));
                long it = escape_count(px, py, max_iter);
                long r = 0L;
                long g = 0L;
                long b = 0L;
                if ((it >= max_iter)) {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                } else {
                    double t = (((double)(it)) / ((double)(max_iter)));
                    r = __pytra_int((255.0 * (t * t)));
                    g = __pytra_int((255.0 * t));
                    b = __pytra_int((255.0 * (1.0 - t)));
                }
                pixels.add(r);
                pixels.add(g);
                pixels.add(b);
            }
        }
        return pixels;
    }

    public static void run_mandelbrot() {
        long width = 1600L;
        long height = 1200L;
        long max_iter = 1000L;
        String out_path = "sample/out/01_mandelbrot.png";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Long> pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2);
        __pytra_noop(out_path, width, height, pixels);
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("size:") + " " + String.valueOf(width) + " " + String.valueOf("x") + " " + String.valueOf(height));
        System.out.println(String.valueOf("max_iter:") + " " + String.valueOf(max_iter));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_mandelbrot();
    }
}
