final class _06_julia_parameter_sweep {
    private _06_julia_parameter_sweep() {
    }


    // 06: Sample that sweeps Julia-set parameters and outputs a GIF.

    public static java.util.ArrayList<Long> julia_palette() {
        java.util.ArrayList<Long> palette = PyRuntime.__pytra_bytearray(256L * 3L);
        palette.set((int)((((0L) < 0L) ? (((long)(palette.size())) + (0L)) : (0L))), 0L);
        palette.set((int)((((1L) < 0L) ? (((long)(palette.size())) + (1L)) : (1L))), 0L);
        palette.set((int)((((2L) < 0L) ? (((long)(palette.size())) + (2L)) : (2L))), 0L);
        for (long i = 1L; i < 256L; i += 1L) {
            double t = (((double)(i - 1L))) / 254.0;
            long r = PyRuntime.__pytra_int(255.0 * (9.0 * (1.0 - t) * t * t * t));
            long g = PyRuntime.__pytra_int(255.0 * (15.0 * (1.0 - t) * (1.0 - t) * t * t));
            long b = PyRuntime.__pytra_int(255.0 * (8.5 * (1.0 - t) * (1.0 - t) * (1.0 - t) * t));
            palette.set((int)((((i * 3L + 0L) < 0L) ? (((long)(palette.size())) + (i * 3L + 0L)) : (i * 3L + 0L))), r);
            palette.set((int)((((i * 3L + 1L) < 0L) ? (((long)(palette.size())) + (i * 3L + 1L)) : (i * 3L + 1L))), g);
            palette.set((int)((((i * 3L + 2L) < 0L) ? (((long)(palette.size())) + (i * 3L + 2L)) : (i * 3L + 2L))), b);
        }
        return PyRuntime.__pytra_bytearray(palette);
    }

    public static java.util.ArrayList<Long> render_frame(long width, long height, double cr, double ci, long max_iter, long phase) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(width * height);
        for (long y = 0L; y < height; y += 1L) {
            long row_base = y * width;
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
                    zy = 2.0 * zx * zy + ci;
                    zx = zx2 - zy2 + cr;
                    i += 1L;
                }
                if (((i) >= (max_iter))) {
                    frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), 0L);
                } else {
                    long color_index = 1L + (i * 224L / max_iter + phase) % 255L;
                    frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), color_index);
                }
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_06_julia_parameter_sweep() {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        long max_iter = 180L;
        String out_path = "sample/out/06_julia_parameter_sweep.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        double center_cr = (-(0.745));
        double center_ci = 0.186;
        double radius_cr = 0.12;
        double radius_ci = 0.1;
        long start_offset = 20L;
        long phase_offset = 180L;
        for (long i = 0L; i < frames_n; i += 1L) {
            double t = ((double)((i + start_offset) % frames_n)) / ((double)(frames_n));
            double angle = 2.0 * math.pi * t;
            double cr = center_cr + radius_cr * math.cos(angle);
            double ci = center_ci + radius_ci * math.sin(angle);
            long phase = (phase_offset + i * 5L) % 255L;
            frames.add(render_frame(width, height, cr, ci, max_iter, phase));
        }
        gif.save_gif(out_path, width, height, frames, julia_palette(), 8L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_06_julia_parameter_sweep();
    }
}
