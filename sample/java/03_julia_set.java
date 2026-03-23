final class _03_julia_set {
    private _03_julia_set() {
    }


    // 03: Sample that outputs a Julia set as a PNG image.
    // Implemented with simple loop-centric logic for transpilation compatibility.

    public static java.util.ArrayList<Long> render_julia(long width, long height, long max_iter, double cx, double cy) {
        java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();
        for (long y = 0L; y < height; y += 1L) {
            double zy0 = (-(1.2)) + 2.4 * (((double)(y)) / (((double)(height - 1L))));
            for (long x = 0L; x < width; x += 1L) {
                double zx = (-(1.8)) + 3.6 * (((double)(x)) / (((double)(width - 1L))));
                double zy = zy0;
                long i = 0L;
                while (((i) < (max_iter))) {
                    double zx2 = zx * zx;
                    double zy2 = zy * zy;
                    if (((zx2 + zy2) > (4.0))) {
                        break;
                    }
                    zy = 2.0 * zx * zy + cy;
                    zx = zx2 - zy2 + cx;
                    i += 1L;
                }
                long r = 0L;
                long g = 0L;
                long b = 0L;
                if (((i) >= (max_iter))) {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                } else {
                    double t = ((double)(i)) / ((double)(max_iter));
                    r = PyRuntime.__pytra_int(255.0 * (0.2 + 0.8 * t));
                    g = PyRuntime.__pytra_int(255.0 * (0.1 + 0.9 * (t * t)));
                    b = PyRuntime.__pytra_int(255.0 * (1.0 - t));
                }
                pixels.add(r);
                pixels.add(g);
                pixels.add(b);
            }
        }
        return pixels;
    }

    public static void run_julia() {
        long width = 3840L;
        long height = 2160L;
        long max_iter = 20000L;
        String out_path = "sample/out/03_julia_set.png";
        double start = time.perf_counter();
        java.util.ArrayList<Long> pixels = render_julia(width, height, max_iter, (-(0.8)), 0.156);
        png.write_rgb_png(out_path, width, height, pixels);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("size:") + " " + String.valueOf(width) + " " + String.valueOf("x") + " " + String.valueOf(height));
        System.out.println(String.valueOf("max_iter:") + " " + String.valueOf(max_iter));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_julia();
    }
}
