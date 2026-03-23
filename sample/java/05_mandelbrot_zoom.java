final class _05_mandelbrot_zoom {
    private _05_mandelbrot_zoom() {
    }


    // 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

    public static java.util.ArrayList<Long> render_frame(long width, long height, double center_x, double center_y, double scale, long max_iter) {
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(width * height);
        for (long y = 0L; y < height; y += 1L) {
            long row_base = y * width;
            double cy = center_y + (((double)(y)) - ((double)(height)) * 0.5) * scale;
            for (long x = 0L; x < width; x += 1L) {
                double cx = center_x + (((double)(x)) - ((double)(width)) * 0.5) * scale;
                double zx = 0.0;
                double zy = 0.0;
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
                frame.set((int)((((row_base + x) < 0L) ? (((long)(frame.size())) + (row_base + x)) : (row_base + x))), PyRuntime.__pytra_int(255.0 * ((double)(i)) / ((double)(max_iter))));
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_05_mandelbrot_zoom() {
        long width = 320L;
        long height = 240L;
        long frame_count = 48L;
        long max_iter = 110L;
        double center_x = (-(0.743643887037151));
        double center_y = 0.13182590420533;
        double base_scale = 3.2 / ((double)(width));
        double zoom_per_frame = 0.93;
        String out_path = "sample/out/05_mandelbrot_zoom.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        double scale = base_scale;
        for (long __ = 0L; __ < frame_count; __ += 1L) {
            frames.add(render_frame(width, height, center_x, center_y, scale, max_iter));
            scale *= zoom_per_frame;
        }
        gif.save_gif(out_path, width, height, frames, gif.grayscale_palette(), 5L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frame_count));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_05_mandelbrot_zoom();
    }
}
