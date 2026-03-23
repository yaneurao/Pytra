final class _01_mandelbrot {
    private _01_mandelbrot() {
    }


    // 01: Sample that outputs the Mandelbrot set as a PNG image.
    // Syntax is kept straightforward with future transpilation in mind.

    public static long escape_count(double cx, double cy, long max_iter) {
        double x = 0.0;
        double y = 0.0;
        for (long i = 0L; i < max_iter; i += 1L) {
            double x2 = x * x;
            double y2 = y * y;
            if (((x2 + y2) > (4.0))) {
                return i;
            }
            y = 2.0 * x * y + cy;
            x = x2 - y2 + cx;
        }
        return max_iter;
    }

    public static Object color_map(long iter_count, long max_iter) {
        if (((iter_count) >= (max_iter))) {
            return new java.util.ArrayList<Object>(java.util.Arrays.asList(0L, 0L, 0L));
        }
        double t = ((double)(iter_count)) / ((double)(max_iter));
        long r = PyRuntime.__pytra_int(255.0 * (t * t));
        long g = PyRuntime.__pytra_int(255.0 * t);
        long b = PyRuntime.__pytra_int(255.0 * (1.0 - t));
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(r, g, b));
    }

    public static java.util.ArrayList<Long> render_mandelbrot(long width, long height, long max_iter, double x_min, double x_max, double y_min, double y_max) {
        java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();
        for (long y = 0L; y < height; y += 1L) {
            double py = y_min + (y_max - y_min) * (((double)(y)) / (((double)(height - 1L))));
            for (long x = 0L; x < width; x += 1L) {
                double px = x_min + (x_max - x_min) * (((double)(x)) / (((double)(width - 1L))));
                long it = escape_count(px, py, max_iter);
                long r = 0L;
                long g = 0L;
                long b = 0L;
                if (((it) >= (max_iter))) {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                } else {
                    double t = ((double)(it)) / ((double)(max_iter));
                    r = PyRuntime.__pytra_int(255.0 * (t * t));
                    g = PyRuntime.__pytra_int(255.0 * t);
                    b = PyRuntime.__pytra_int(255.0 * (1.0 - t));
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
        double start = time.perf_counter();
        java.util.ArrayList<Long> pixels = render_mandelbrot(width, height, max_iter, (-(2.2)), 1.0, (-(1.2)), 1.2);
        png.write_rgb_png(out_path, width, height, pixels);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("size:") + " " + String.valueOf(width) + " " + String.valueOf("x") + " " + String.valueOf(height));
        System.out.println(String.valueOf("max_iter:") + " " + String.valueOf(max_iter));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_mandelbrot();
    }
}
