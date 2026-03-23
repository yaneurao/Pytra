final class _16_glass_sculpture_chaos {
    private _16_glass_sculpture_chaos() {
    }


    // 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.

    public static double clamp01(double v) {
        if (((v) < (0.0))) {
            return 0.0;
        }
        if (((v) > (1.0))) {
            return 1.0;
        }
        return v;
    }

    public static double dot(double ax, double ay, double az, double bx, double by, double bz) {
        return ax * bx + ay * by + az * bz;
    }

    public static double length(double x, double y, double z) {
        return math.sqrt(x * x + y * y + z * z);
    }

    public static Object normalize(double x, double y, double z) {
        double l = length(x, y, z);
        if (((l) < (1e-09))) {
            return new java.util.ArrayList<Object>(java.util.Arrays.asList(0.0, 0.0, 0.0));
        }
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(x / l, y / l, z / l));
    }

    public static Object reflect(double ix, double iy, double iz, double nx, double ny, double nz) {
        double d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(ix - d * nx, iy - d * ny, iz - d * nz));
    }

    public static Object refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta) {
        double cosi = (-(dot(ix, iy, iz, nx, ny, nz)));
        double sint2 = eta * eta * (1.0 - cosi * cosi);
        if (((sint2) > (1.0))) {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        double cost = math.sqrt(1.0 - sint2);
        double k = eta * cosi - cost;
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz));
    }

    public static double schlick(double cos_theta, double f0) {
        double m = 1.0 - cos_theta;
        return f0 + (1.0 - f0) * (m * m * m * m * m);
    }

    public static Object sky_color(double dx, double dy, double dz, double tphase) {
        double t = 0.5 * (dy + 1.0);
        double r = 0.06 + 0.2 * t;
        double g = 0.1 + 0.25 * t;
        double b = 0.16 + 0.45 * t;
        double band = 0.5 + 0.5 * math.sin(8.0 * dx + 6.0 * dz + tphase);
        r += 0.08 * band;
        g += 0.05 * band;
        b += 0.12 * band;
        return new java.util.ArrayList<Object>(java.util.Arrays.asList(clamp01(r), clamp01(g), clamp01(b)));
    }

    public static double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius) {
        double lx = ox - cx;
        double ly = oy - cy;
        double lz = oz - cz;
        double b = lx * dx + ly * dy + lz * dz;
        double c = lx * lx + ly * ly + lz * lz - radius * radius;
        double h = b * b - c;
        if (((h) < (0.0))) {
            return (-(1.0));
        }
        double s = math.sqrt(h);
        double t0 = (-(b)) - s;
        if (((t0) > (0.0001))) {
            return t0;
        }
        double t1 = (-(b)) + s;
        if (((t1) > (0.0001))) {
            return t1;
        }
        return (-(1.0));
    }

    public static java.util.ArrayList<Long> palette_332() {
        java.util.ArrayList<Long> p = PyRuntime.__pytra_bytearray(256L * 3L);
        for (long i = 0L; i < 256L; i += 1L) {
            long r = i >> 5L & 7L;
            long g = i >> 2L & 7L;
            long b = i & 3L;
            p.set((int)((((i * 3L + 0L) < 0L) ? (((long)(p.size())) + (i * 3L + 0L)) : (i * 3L + 0L))), PyRuntime.__pytra_int(((double)(255L * r)) / ((double)(7L))));
            p.set((int)((((i * 3L + 1L) < 0L) ? (((long)(p.size())) + (i * 3L + 1L)) : (i * 3L + 1L))), PyRuntime.__pytra_int(((double)(255L * g)) / ((double)(7L))));
            p.set((int)((((i * 3L + 2L) < 0L) ? (((long)(p.size())) + (i * 3L + 2L)) : (i * 3L + 2L))), PyRuntime.__pytra_int(((double)(255L * b)) / ((double)(3L))));
        }
        return PyRuntime.__pytra_bytearray(p);
    }

    public static long quantize_332(double r, double g, double b) {
        long rr = PyRuntime.__pytra_int(clamp01(r) * 255.0);
        long gg = PyRuntime.__pytra_int(clamp01(g) * 255.0);
        long bb = PyRuntime.__pytra_int(clamp01(b) * 255.0);
        return (rr >> 5L << 5L) + (gg >> 5L << 2L) + (bb >> 6L);
    }

    public static java.util.ArrayList<Long> render_frame(long width, long height, long frame_id, long frames_n) {
        double t = ((double)(frame_id)) / ((double)(frames_n));
        double tphase = 2.0 * math.pi * t;
        double cam_r = 3.0;
        double cam_x = cam_r * math.cos(tphase * 0.9);
        double cam_y = 1.1 + 0.25 * math.sin(tphase * 0.6);
        double cam_z = cam_r * math.sin(tphase * 0.9);
        double look_x = 0.0;
        double look_y = 0.35;
        double look_z = 0.0;
        java.util.ArrayList<Object> __tuple_0 = ((java.util.ArrayList<Object>)(Object)(normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z)));
        double fwd_x = ((Double)(__tuple_0.get(0)));
        double fwd_y = ((Double)(__tuple_0.get(1)));
        double fwd_z = ((Double)(__tuple_0.get(2)));
        java.util.ArrayList<Object> __tuple_1 = ((java.util.ArrayList<Object>)(Object)(normalize(fwd_z, 0.0, (-(fwd_x)))));
        double right_x = ((Double)(__tuple_1.get(0)));
        double right_y = ((Double)(__tuple_1.get(1)));
        double right_z = ((Double)(__tuple_1.get(2)));
        java.util.ArrayList<Object> __tuple_2 = ((java.util.ArrayList<Object>)(Object)(normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x)));
        double up_x = ((Double)(__tuple_2.get(0)));
        double up_y = ((Double)(__tuple_2.get(1)));
        double up_z = ((Double)(__tuple_2.get(2)));
        double s0x = 0.9 * math.cos(1.3 * tphase);
        double s0y = 0.15 + 0.35 * math.sin(1.7 * tphase);
        double s0z = 0.9 * math.sin(1.3 * tphase);
        double s1x = 1.2 * math.cos(1.3 * tphase + 2.094);
        double s1y = 0.1 + 0.4 * math.sin(1.1 * tphase + 0.8);
        double s1z = 1.2 * math.sin(1.3 * tphase + 2.094);
        double s2x = 1.0 * math.cos(1.3 * tphase + 4.188);
        double s2y = 0.2 + 0.3 * math.sin(1.5 * tphase + 1.9);
        double s2z = 1.0 * math.sin(1.3 * tphase + 4.188);
        double lr = 0.35;
        double lx = 2.4 * math.cos(tphase * 1.8);
        double ly = 1.8 + 0.8 * math.sin(tphase * 1.2);
        double lz = 2.4 * math.sin(tphase * 1.8);
        java.util.ArrayList<Long> frame = PyRuntime.__pytra_bytearray(width * height);
        double aspect = ((double)(width)) / ((double)(height));
        double fov = 1.25;
        for (long py = 0L; py < height; py += 1L) {
            long row_base = py * width;
            double sy = 1.0 - 2.0 * (((double)(py)) + 0.5) / ((double)(height));
            for (long px = 0L; px < width; px += 1L) {
                double sx = (2.0 * (((double)(px)) + 0.5) / ((double)(width)) - 1.0) * aspect;
                double rx = fwd_x + fov * (sx * right_x + sy * up_x);
                double ry = fwd_y + fov * (sx * right_y + sy * up_y);
                double rz = fwd_z + fov * (sx * right_z + sy * up_z);
                java.util.ArrayList<Object> __tuple_3 = ((java.util.ArrayList<Object>)(Object)(normalize(rx, ry, rz)));
                double dx = ((Double)(__tuple_3.get(0)));
                double dy = ((Double)(__tuple_3.get(1)));
                double dz = ((Double)(__tuple_3.get(2)));
                double best_t = 1000000000.0;
                long hit_kind = 0L;
                double r = 0.0;
                double g = 0.0;
                double b = 0.0;
                if (((dy) < ((-(1e-06))))) {
                    double tf = ((-(1.2)) - cam_y) / dy;
                    if ((((tf) > (0.0001)) && ((tf) < (best_t)))) {
                        best_t = tf;
                        hit_kind = 1L;
                    }
                }
                double t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if ((((t0) > (0.0)) && ((t0) < (best_t)))) {
                    best_t = t0;
                    hit_kind = 2L;
                }
                double t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if ((((t1) > (0.0)) && ((t1) < (best_t)))) {
                    best_t = t1;
                    hit_kind = 3L;
                }
                double t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if ((((t2) > (0.0)) && ((t2) < (best_t)))) {
                    best_t = t2;
                    hit_kind = 4L;
                }
                double glow = 0.0;
                double hx = 0.0;
                double hz = 0.0;
                double ldx = 0.0;
                double ldy = 0.0;
                double ldz = 0.0;
                double lxv = 0.0;
                double lyv = 0.0;
                double lzv = 0.0;
                double ndotl = 0.0;
                if (((hit_kind) == (0L))) {
                    java.util.ArrayList<Object> __tuple_4 = ((java.util.ArrayList<Object>)(Object)(sky_color(dx, dy, dz, tphase)));
                    r = ((Double)(__tuple_4.get(0)));
                    g = ((Double)(__tuple_4.get(1)));
                    b = ((Double)(__tuple_4.get(2)));
                } else {
                    if (((hit_kind) == (1L))) {
                        hx = cam_x + best_t * dx;
                        hz = cam_z + best_t * dz;
                        long cx_i = PyRuntime.__pytra_int(math.floor(hx * 2.0));
                        long cz_i = PyRuntime.__pytra_int(math.floor(hz * 2.0));
                        long checker = (((((cx_i + cz_i) % 2L) == (0L))) ? (0L) : (1L));
                        double base_r = ((((checker) == (0L))) ? (0.1) : (0.04));
                        double base_g = ((((checker) == (0L))) ? (0.11) : (0.05));
                        double base_b = ((((checker) == (0L))) ? (0.13) : (0.08));
                        lxv = lx - hx;
                        lyv = ly - (-(1.2));
                        lzv = lz - hz;
                        java.util.ArrayList<Object> __tuple_5 = ((java.util.ArrayList<Object>)(Object)(normalize(lxv, lyv, lzv)));
                        ldx = ((Double)(__tuple_5.get(0)));
                        ldy = ((Double)(__tuple_5.get(1)));
                        ldz = ((Double)(__tuple_5.get(2)));
                        ndotl = Math.max(ldy, 0.0);
                        double ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                        glow = 8.0 / (1.0 + ldist2);
                        r = base_r + 0.8 * glow + 0.2 * ndotl;
                        g = base_g + 0.5 * glow + 0.18 * ndotl;
                        b = base_b + 1.0 * glow + 0.24 * ndotl;
                    } else {
                        double cx = 0.0;
                        double cy = 0.0;
                        double cz = 0.0;
                        double rad = 1.0;
                        if (((hit_kind) == (2L))) {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        } else {
                            if (((hit_kind) == (3L))) {
                                cx = s1x;
                                cy = s1y;
                                cz = s1z;
                                rad = 0.72;
                            } else {
                                cx = s2x;
                                cy = s2y;
                                cz = s2z;
                                rad = 0.58;
                            }
                        }
                        hx = cam_x + best_t * dx;
                        double hy = cam_y + best_t * dy;
                        hz = cam_z + best_t * dz;
                        java.util.ArrayList<Object> __tuple_6 = ((java.util.ArrayList<Object>)(Object)(normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad)));
                        double nx = ((Double)(__tuple_6.get(0)));
                        double ny = ((Double)(__tuple_6.get(1)));
                        double nz = ((Double)(__tuple_6.get(2)));
                        java.util.ArrayList<Object> __tuple_7 = ((java.util.ArrayList<Object>)(Object)(reflect(dx, dy, dz, nx, ny, nz)));
                        double rdx = ((Double)(__tuple_7.get(0)));
                        double rdy = ((Double)(__tuple_7.get(1)));
                        double rdz = ((Double)(__tuple_7.get(2)));
                        java.util.ArrayList<Object> __tuple_8 = ((java.util.ArrayList<Object>)(Object)(refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45)));
                        double tdx = ((Double)(__tuple_8.get(0)));
                        double tdy = ((Double)(__tuple_8.get(1)));
                        double tdz = ((Double)(__tuple_8.get(2)));
                        java.util.ArrayList<Object> __tuple_9 = ((java.util.ArrayList<Object>)(Object)(sky_color(rdx, rdy, rdz, tphase)));
                        double sr = ((Double)(__tuple_9.get(0)));
                        double sg = ((Double)(__tuple_9.get(1)));
                        double sb = ((Double)(__tuple_9.get(2)));
                        java.util.ArrayList<Object> __tuple_10 = ((java.util.ArrayList<Object>)(Object)(sky_color(tdx, tdy, tdz, tphase + 0.8)));
                        double tr = ((Double)(__tuple_10.get(0)));
                        double tg = ((Double)(__tuple_10.get(1)));
                        double tb = ((Double)(__tuple_10.get(2)));
                        double cosi = Math.max((-(dx * nx + dy * ny + dz * nz)), 0.0);
                        double fr = schlick(cosi, 0.04);
                        r = tr * (1.0 - fr) + sr * fr;
                        g = tg * (1.0 - fr) + sg * fr;
                        b = tb * (1.0 - fr) + sb * fr;
                        lxv = lx - hx;
                        lyv = ly - hy;
                        lzv = lz - hz;
                        java.util.ArrayList<Object> __tuple_11 = ((java.util.ArrayList<Object>)(Object)(normalize(lxv, lyv, lzv)));
                        ldx = ((Double)(__tuple_11.get(0)));
                        ldy = ((Double)(__tuple_11.get(1)));
                        ldz = ((Double)(__tuple_11.get(2)));
                        ndotl = Math.max(nx * ldx + ny * ldy + nz * ldz, 0.0);
                        java.util.ArrayList<Object> __tuple_12 = ((java.util.ArrayList<Object>)(Object)(normalize(ldx - dx, ldy - dy, ldz - dz)));
                        double hvx = ((Double)(__tuple_12.get(0)));
                        double hvy = ((Double)(__tuple_12.get(1)));
                        double hvz = ((Double)(__tuple_12.get(2)));
                        double ndoth = Math.max(nx * hvx + ny * hvy + nz * hvz, 0.0);
                        double spec = ndoth * ndoth;
                        spec = spec * spec;
                        spec = spec * spec;
                        spec = spec * spec;
                        glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                        r += 0.2 * ndotl + 0.8 * spec + 0.45 * glow;
                        g += 0.18 * ndotl + 0.6 * spec + 0.35 * glow;
                        b += 0.26 * ndotl + 1.0 * spec + 0.65 * glow;
                        if (((hit_kind) == (2L))) {
                            r *= 0.95;
                            g *= 1.05;
                            b *= 1.1;
                        } else {
                            if (((hit_kind) == (3L))) {
                                r *= 1.08;
                                g *= 0.98;
                                b *= 1.04;
                            } else {
                                r *= 1.02;
                                g *= 1.1;
                                b *= 0.95;
                            }
                        }
                    }
                }
                r = math.sqrt(clamp01(r));
                g = math.sqrt(clamp01(g));
                b = math.sqrt(clamp01(b));
                frame.set((int)((((row_base + px) < 0L) ? (((long)(frame.size())) + (row_base + px)) : (row_base + px))), quantize_332(r, g, b));
            }
        }
        return PyRuntime.__pytra_bytearray(frame);
    }

    public static void run_16_glass_sculpture_chaos() {
        long width = 320L;
        long height = 240L;
        long frames_n = 72L;
        String out_path = "sample/out/16_glass_sculpture_chaos.gif";
        double start = time.perf_counter();
        java.util.ArrayList<java.util.ArrayList<Long>> frames = new java.util.ArrayList<java.util.ArrayList<Long>>();
        for (long i = 0L; i < frames_n; i += 1L) {
            frames.add(render_frame(width, height, i, frames_n));
        }
        gif.save_gif(out_path, width, height, frames, palette_332(), 6L, 0L);
        double elapsed = time.perf_counter() - start;
        System.out.println(String.valueOf("output:") + " " + String.valueOf(out_path));
        System.out.println(String.valueOf("frames:") + " " + String.valueOf(frames_n));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_16_glass_sculpture_chaos();
    }
}
