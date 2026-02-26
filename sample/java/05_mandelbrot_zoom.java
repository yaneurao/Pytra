// Auto-generated Java native source from EAST3.
public final class Pytra_05_mandelbrot_zoom {
    private Pytra_05_mandelbrot_zoom() {
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

    public static java.util.ArrayList<Long> render_frame(long width, long height, double center_x, double center_y, double scale, long max_iter) {
        java.util.ArrayList<Long> frame = __pytra_bytearray((width * height));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            long row_base = (y * width);
            double cy = (center_y + ((((double)(y)) - (((double)(height)) * 0.5)) * scale));
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                double cx = (center_x + ((((double)(x)) - (((double)(width)) * 0.5)) * scale));
                double zx = 0.0;
                double zy = 0.0;
                long i = 0L;
                while ((i < max_iter)) {
                    double zx2 = (zx * zx);
                    double zy2 = (zy * zy);
                    if (((zx2 + zy2) > 4.0)) {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + cy);
                    zx = ((zx2 - zy2) + cx);
                    i += 1L;
                }
                frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), __pytra_int(((255.0 * ((double)(i))) / ((double)(max_iter)))));
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_05_mandelbrot_zoom() {
        long width = 320L;
        long height = 240L;
        long frame_count = 48L;
        long max_iter = 110L;
        double center_x = (-0.743643887037151);
        double center_y = 0.13182590420533;
        double base_scale = (3.2 / ((double)(width)));
        double zoom_per_frame = 0.93;
        String out_path = "sample/out/05_mandelbrot_zoom.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        double scale = base_scale;
        long __step_0 = 1L;
        for (long __ = 0L; (__step_0 >= 0L) ? (__ < frame_count) : (__ > frame_count); __ += __step_0) {
            frames.add(render_frame(width, height, center_x, center_y, scale, max_iter));
            scale *= zoom_per_frame;
        }
        __pytra_noop(out_path, width, height, frames, new java.util.ArrayList<Long>());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frame_count));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_05_mandelbrot_zoom();
    }
}
