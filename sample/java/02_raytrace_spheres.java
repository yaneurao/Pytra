// Auto-generated Java native source from EAST3.
public final class Pytra_02_raytrace_spheres {
    private Pytra_02_raytrace_spheres() {
    }


    public static double clamp01(double v) {
        if ((v < 0.0)) {
            return 0.0;
        }
        if ((v > 1.0)) {
            return 1.0;
        }
        return v;
    }

    public static double hit_sphere(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double r) {
        double lx = (ox - cx);
        double ly = (oy - cy);
        double lz = (oz - cz);
        double a = (((dx * dx) + (dy * dy)) + (dz * dz));
        double b = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)));
        double c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r));
        double d = ((b * b) - ((4.0 * a) * c));
        if ((d < 0.0)) {
            return (-1.0);
        }
        double sd = Math.sqrt(d);
        double t0 = (((-b) - sd) / (2.0 * a));
        double t1 = (((-b) + sd) / (2.0 * a));
        if ((t0 > 0.001)) {
            return t0;
        }
        if ((t1 > 0.001)) {
            return t1;
        }
        return (-1.0);
    }

    public static java.util.ArrayList<Long> render(long width, long height, long aa) {
        java.util.ArrayList<Long> pixels = new java.util.ArrayList<Long>();
        double ox = 0.0;
        double oy = 0.0;
        double oz = (-3.0);
        double lx = (-0.4);
        double ly = 0.8;
        double lz = (-0.45);
        double __hoisted_cast_1 = ((double)(aa));
        double __hoisted_cast_2 = ((double)((height - 1L)));
        double __hoisted_cast_3 = ((double)((width - 1L)));
        double __hoisted_cast_4 = ((double)(height));
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                long ar = 0L;
                long ag = 0L;
                long ab = 0L;
                long __step_2 = 1L;
                for (long ay = 0L; (__step_2 >= 0L) ? (ay < aa) : (ay > aa); ay += __step_2) {
                    long __step_3 = 1L;
                    for (long ax = 0L; (__step_3 >= 0L) ? (ax < aa) : (ax > aa); ax += __step_3) {
                        double fy = ((((double)(y)) + ((((double)(ay)) + 0.5) / __hoisted_cast_1)) / __hoisted_cast_2);
                        double fx = ((((double)(x)) + ((((double)(ax)) + 0.5) / __hoisted_cast_1)) / __hoisted_cast_3);
                        double sy = (1.0 - (2.0 * fy));
                        double sx = (((2.0 * fx) - 1.0) * (((double)(width)) / __hoisted_cast_4));
                        double dx = sx;
                        double dy = sy;
                        double dz = 1.0;
                        double inv_len = (1.0 / Math.sqrt((((dx * dx) + (dy * dy)) + (dz * dz))));
                        dx *= inv_len;
                        dy *= inv_len;
                        dz *= inv_len;
                        double t_min = 1e+30;
                        long hit_id = (-1L);
                        double t = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8);
                        if (((t > 0.0) && (t < t_min))) {
                            t_min = t;
                            hit_id = 0L;
                        }
                        t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                        if (((t > 0.0) && (t < t_min))) {
                            t_min = t;
                            hit_id = 1L;
                        }
                        t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0);
                        if (((t > 0.0) && (t < t_min))) {
                            t_min = t;
                            hit_id = 2L;
                        }
                        long r = 0L;
                        long g = 0L;
                        long b = 0L;
                        if ((hit_id >= 0L)) {
                            double px = (ox + (dx * t_min));
                            double py = (oy + (dy * t_min));
                            double pz = (oz + (dz * t_min));
                            double nx = 0.0;
                            double ny = 0.0;
                            double nz = 0.0;
                            if ((hit_id == 0L)) {
                                nx = ((px + 0.8) / 0.8);
                                ny = ((py + 0.2) / 0.8);
                                nz = ((pz - 2.2) / 0.8);
                            } else {
                                if ((hit_id == 1L)) {
                                    nx = ((px - 0.9) / 0.95);
                                    ny = ((py - 0.1) / 0.95);
                                    nz = ((pz - 2.9) / 0.95);
                                } else {
                                    nx = 0.0;
                                    ny = 1.0;
                                    nz = 0.0;
                                }
                            }
                            double diff = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)));
                            diff = clamp01(diff);
                            double base_r = 0.0;
                            double base_g = 0.0;
                            double base_b = 0.0;
                            if ((hit_id == 0L)) {
                                base_r = 0.95;
                                base_g = 0.35;
                                base_b = 0.25;
                            } else {
                                if ((hit_id == 1L)) {
                                    base_r = 0.25;
                                    base_g = 0.55;
                                    base_b = 0.95;
                                } else {
                                    long checker = (PyRuntime.__pytra_int(((px + 50.0) * 0.8)) + PyRuntime.__pytra_int(((pz + 50.0) * 0.8)));
                                    if (((checker % 2L) == 0L)) {
                                        base_r = 0.85;
                                        base_g = 0.85;
                                        base_b = 0.85;
                                    } else {
                                        base_r = 0.2;
                                        base_g = 0.2;
                                        base_b = 0.2;
                                    }
                                }
                            }
                            double shade = (0.12 + (0.88 * diff));
                            r = PyRuntime.__pytra_int((255.0 * clamp01((base_r * shade))));
                            g = PyRuntime.__pytra_int((255.0 * clamp01((base_g * shade))));
                            b = PyRuntime.__pytra_int((255.0 * clamp01((base_b * shade))));
                        } else {
                            double tsky = (0.5 * (dy + 1.0));
                            r = PyRuntime.__pytra_int((255.0 * (0.65 + (0.2 * tsky))));
                            g = PyRuntime.__pytra_int((255.0 * (0.75 + (0.18 * tsky))));
                            b = PyRuntime.__pytra_int((255.0 * (0.9 + (0.08 * tsky))));
                        }
                        ar += r;
                        ag += g;
                        ab += b;
                    }
                }
                long samples = (aa * aa);
                pixels.add((ar / samples));
                pixels.add((ag / samples));
                pixels.add((ab / samples));
            }
        }
        return pixels;
    }

    public static void run_raytrace() {
        long width = 1600L;
        long height = 900L;
        long aa = 2L;
        String out_path = "sample/out/02_raytrace_spheres.png";
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Long> pixels = render(width, height, aa);
        PyRuntime.__pytra_noop(out_path, width, height, pixels);
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("size:") + " " + String.valueOf(width) + " " + String.valueOf("x") + " " + String.valueOf(height));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_raytrace();
    }
}
