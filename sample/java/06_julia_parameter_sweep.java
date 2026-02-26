// Auto-generated Java native source from EAST3.
public final class Pytra_06_julia_parameter_sweep {
    private Pytra_06_julia_parameter_sweep() {
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

    public static java.util.ArrayList<Long> julia_palette() {
        java.util.ArrayList<Long> palette = __pytra_bytearray((256L * 3L));
        palette.set((int)((((0L) < 0L) ? (((long)(palette.size())) + (0L)) : (0L))), 0L);
        palette.set((int)((((1L) < 0L) ? (((long)(palette.size())) + (1L)) : (1L))), 0L);
        palette.set((int)((((2L) < 0L) ? (((long)(palette.size())) + (2L)) : (2L))), 0L);
        long __step_0 = 1L;
        for (long i = 1L; (__step_0 >= 0L) ? (i < 256L) : (i > 256L); i += __step_0) {
            double t = (((double)((i - 1L))) / 254.0);
            long r = __pytra_int((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)));
            long g = __pytra_int((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)));
            long b = __pytra_int((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)));
            palette.set((int)((((((i * 3L) + 0L)) < 0L) ? (((long)(palette.size())) + (((i * 3L) + 0L))) : (((i * 3L) + 0L)))), r);
            palette.set((int)((((((i * 3L) + 1L)) < 0L) ? (((long)(palette.size())) + (((i * 3L) + 1L))) : (((i * 3L) + 1L)))), g);
            palette.set((int)((((((i * 3L) + 2L)) < 0L) ? (((long)(palette.size())) + (((i * 3L) + 2L))) : (((i * 3L) + 2L)))), b);
        }
        return new java.util.ArrayList<Long>(palette);
    }

    public static java.util.ArrayList<Long> render_frame(long width, long height, double cr, double ci, long max_iter, long phase) {
        java.util.ArrayList<Long> frame = __pytra_bytearray((width * height));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            long row_base = (y * width);
            double zy0 = ((-1.2) + (2.4 * (((double)(y)) / ((double)((height - 1L))))));
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                double zx = ((-1.8) + (3.6 * (((double)(x)) / ((double)((width - 1L))))));
                double zy = zy0;
                long i = 0L;
                while ((i < max_iter)) {
                    double zx2 = (zx * zx);
                    double zy2 = (zy * zy);
                    if (((zx2 + zy2) > 4.0)) {
                        break;
                    }
                    zy = (((2.0 * zx) * zy) + ci);
                    zx = ((zx2 - zy2) + cr);
                    i += 1L;
                }
                if ((i >= max_iter)) {
                    frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), 0L);
                } else {
                    long color_index = (1L + ((((i * 224L) / max_iter) + phase) % 255L));
                    frame.set((int)(((((row_base + x)) < 0L) ? (((long)(frame.size())) + ((row_base + x))) : ((row_base + x)))), color_index);
                }
            }
        }
        return new java.util.ArrayList<Long>(frame);
    }

    public static void run_06_julia_parameter_sweep() {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        long max_iter = 180L;
        String out_path = "sample/out/06_julia_parameter_sweep.gif";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> frames = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        double center_cr = (-0.745);
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.1;
        long start_offset = 20L;
        long phase_offset = 180L;
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < frames_n) : (i > frames_n); i += __step_0) {
            double t = (((double)(((i + start_offset) % frames_n))) / ((double)(frames_n)));
            double angle = ((2.0 * Math.PI) * t);
            double cr = (center_cr + (radius_cr * Math.cos(angle)));
            double ci = (center_ci + (radius_ci * Math.sin(angle)));
            long phase = ((phase_offset + (i * 5L)) % 255L);
            frames.add(render_frame(width, height, cr, ci, max_iter, phase));
        }
        __pytra_noop(out_path, width, height, frames, julia_palette());
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_06_julia_parameter_sweep();
    }
}
