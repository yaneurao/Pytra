public final class Pytra_04_orbit_trap_julia {
    private Pytra_04_orbit_trap_julia() {
    }


    // 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

    public static java.util.ArrayList<Long> render_orbit_trap_julia(long width, long height, long max_iter, double cx, double cy) {
        java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();
        double __hoisted_cast_1 = ((double)(height - 1L));
        double __hoisted_cast_2 = ((double)(width - 1L));
        double __hoisted_cast_3 = ((double)(max_iter));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            double zy0 = (-1.3) + 2.6 * (((double)(y)) / __hoisted_cast_1);
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                double zx = (-1.9) + 3.8 * (((double)(x)) / __hoisted_cast_2);
                double zy = zy0;
                double trap = 1000000000.0;
                long i = 0L;
                while ((i < max_iter)) {
                    double ax = zx;
                    if ((ax < 0.0)) {
                        ax = (-ax);
                    }
                    double ay = zy;
                    if ((ay < 0.0)) {
                        ay = (-ay);
                    }
                    double dxy = zx - zy;
                    if ((dxy < 0.0)) {
                        dxy = (-dxy);
                    }
                    if ((ax < trap)) {
                        trap = ax;
                    }
                    if ((ay < trap)) {
                        trap = ay;
                    }
                    if ((dxy < trap)) {
                        trap = dxy;
                    }
                    double zx2 = zx * zx;
                    double zy2 = zy * zy;
                    if ((zx2 + zy2 > 4.0)) {
                        break;
                    }
                    zy = 2.0 * zx * zy + cy;
                    zx = zx2 - zy2 + cx;
                    i += 1L;
                }
                long r = 0L;
                long g = 0L;
                long b = 0L;
                if ((i >= max_iter)) {
                    r = 0L;
                    g = 0L;
                    b = 0L;
                } else {
                    double trap_scaled = trap * 3.2;
                    if ((trap_scaled > 1.0)) {
                        trap_scaled = 1.0;
                    }
                    if ((trap_scaled < 0.0)) {
                        trap_scaled = 0.0;
                    }
                    double t = ((double)(i)) / __hoisted_cast_3;
                    long tone = PyRuntime.__pytra_int(255.0 * (1.0 - trap_scaled));
                    r = PyRuntime.__pytra_int(((double)(tone)) * (0.35 + 0.65 * t));
                    g = PyRuntime.__pytra_int(((double)(tone)) * (0.15 + 0.85 * (1.0 - t)));
                    b = PyRuntime.__pytra_int(255.0 * (0.25 + 0.75 * t));
                    if ((r > 255L)) {
                        r = 255L;
                    }
                    if ((g > 255L)) {
                        g = 255L;
                    }
                    if ((b > 255L)) {
                        b = 255L;
                    }
                }
                pixels.add(r);
                pixels.add(g);
                pixels.add(b);
            }
        }
        return pixels;
    }

    public static void run_04_orbit_trap_julia() {
        long width = 1920L;
        long height = 1080L;
        long max_iter = 1400L;
        String out_path = "sample/out/04_orbit_trap_julia.png";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Long> pixels = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889);
        PyRuntime.__pytra_noop(out_path, width, height, pixels);
        double elapsed = (System.nanoTime() / 1000000000.0) - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("size:") + " " + String.valueOf(width) + " " + String.valueOf("x") + " " + String.valueOf(height));
        System.out.println(String.valueOf("max_iter:") + " " + String.valueOf(max_iter));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_04_orbit_trap_julia();
    }
}
