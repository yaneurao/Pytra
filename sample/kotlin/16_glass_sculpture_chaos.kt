using math;

public static class Program
{
    // 16: Sample that ray-traces chaotic rotation of glass sculptures and outputs a GIF.
    
    public static double clamp01(double v)
    {
        if (v < 0.0) {
            return 0.0;
        }
        if (v > 1.0) {
            return 1.0;
        }
        return v;
    }
    
    public static double dot(double ax, double ay, double az, double bx, double by, double bz)
    {
        return ax * bx + ay * by + az * bz;
    }
    
    public static double length(double x, double y, double z)
    {
        return math.sqrt(x * x + y * y + z * z);
    }
    
    public static (double, double, double) normalize(double x, double y, double z)
    {
        double l = length(x, y, z);
        if (l < 1e-9) {
            return (0.0, 0.0, 0.0);
        }
        return (x / l, y / l, z / l);
    }
    
    public static (double, double, double) reflect(double ix, double iy, double iz, double nx, double ny, double nz)
    {
        double d = dot(ix, iy, iz, nx, ny, nz) * 2.0;
        return (ix - d * nx, iy - d * ny, iz - d * nz);
    }
    
    public static (double, double, double) refract(double ix, double iy, double iz, double nx, double ny, double nz, double eta)
    {
        // Simple IOR-based refraction. Return reflection direction on total internal reflection.
        double cosi = -dot(ix, iy, iz, nx, ny, nz);
        double sint2 = eta * eta * (1.0 - cosi * cosi);
        if (sint2 > 1.0) {
            return reflect(ix, iy, iz, nx, ny, nz);
        }
        unknown cost = math.sqrt(1.0 - sint2);
        unknown k = eta * cosi - cost;
        return (eta * ix + k * nx, eta * iy + k * ny, eta * iz + k * nz);
    }
    
    public static double schlick(double cos_theta, double f0)
    {
        double m = 1.0 - cos_theta;
        return f0 + (1.0 - f0) * m * m * m * m * m;
    }
    
    public static (double, double, double) sky_color(double dx, double dy, double dz, double tphase)
    {
        // Sky gradient + neon band
        double t = 0.5 * (dy + 1.0);
        double r = 0.06 + 0.20 * t;
        double g = 0.10 + 0.25 * t;
        double b = 0.16 + 0.45 * t;
        unknown band = 0.5 + 0.5 * math.sin(8.0 * dx + 6.0 * dz + tphase);
        r += 0.08 * band;
        g += 0.05 * band;
        b += 0.12 * band;
        return (clamp01(r), clamp01(g), clamp01(b));
    }
    
    public static double sphere_intersect(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double radius)
    {
        double lx = ox - cx;
        double ly = oy - cy;
        double lz = oz - cz;
        double b = lx * dx + ly * dy + lz * dz;
        double c = lx * lx + ly * ly + lz * lz - radius * radius;
        double h = b * b - c;
        if (h < 0.0) {
            return -1.0;
        }
        unknown s = math.sqrt(h);
        unknown t0 = -b - s;
        if (t0 > 1e-4) {
            return t0;
        }
        unknown t1 = -b + s;
        if (t1 > 1e-4) {
            return t1;
        }
        return -1.0;
    }
    
    public static List<byte> palette_332()
    {
        // 3-3-2 quantized palette. Lightweight quantization that stays fast after transpilation.
        List<byte> p = bytearray(256 * 3);
        for (long i = 0; i < 256; i += 1) {
            long r = i >> 5 & 7;
            long g = i >> 2 & 7;
            long b = i & 3;
            p[System.Convert.ToInt32(i * 3 + 0)] = System.Convert.ToInt64(255 * r / 7);
            p[System.Convert.ToInt32(i * 3 + 1)] = System.Convert.ToInt64(255 * g / 7);
            p[System.Convert.ToInt32(i * 3 + 2)] = System.Convert.ToInt64(255 * b / 3);
        }
        return bytes(p);
    }
    
    public static long quantize_332(double r, double g, double b)
    {
        long rr = System.Convert.ToInt64(clamp01(r) * 255.0);
        long gg = System.Convert.ToInt64(clamp01(g) * 255.0);
        long bb = System.Convert.ToInt64(clamp01(b) * 255.0);
        return (rr >> 5 << 5) + (gg >> 5 << 2) + (bb >> 6);
    }
    
    public static List<byte> render_frame(long width, long height, long frame_id, long frames_n)
    {
        double t = frame_id / frames_n;
        unknown tphase = 2.0 * math.pi * t;
        
        // Camera slowly orbits.
        double cam_r = 3.0;
        unknown cam_x = cam_r * math.cos(tphase * 0.9);
        unknown cam_y = 1.1 + 0.25 * math.sin(tphase * 0.6);
        unknown cam_z = cam_r * math.sin(tphase * 0.9);
        double look_x = 0.0;
        double look_y = 0.35;
        double look_z = 0.0;
        
        (fwd_x, fwd_y, fwd_z) = normalize(look_x - cam_x, look_y - cam_y, look_z - cam_z);
        (right_x, right_y, right_z) = normalize(fwd_z, 0.0, -fwd_x);
        (up_x, up_y, up_z) = normalize(right_y * fwd_z - right_z * fwd_y, right_z * fwd_x - right_x * fwd_z, right_x * fwd_y - right_y * fwd_x);
        
        // Moving glass sculpture (3 spheres) and an emissive sphere.
        unknown s0x = 0.9 * math.cos(1.3 * tphase);
        unknown s0y = 0.15 + 0.35 * math.sin(1.7 * tphase);
        unknown s0z = 0.9 * math.sin(1.3 * tphase);
        unknown s1x = 1.2 * math.cos(1.3 * tphase + 2.094);
        unknown s1y = 0.10 + 0.40 * math.sin(1.1 * tphase + 0.8);
        unknown s1z = 1.2 * math.sin(1.3 * tphase + 2.094);
        unknown s2x = 1.0 * math.cos(1.3 * tphase + 4.188);
        unknown s2y = 0.20 + 0.30 * math.sin(1.5 * tphase + 1.9);
        unknown s2z = 1.0 * math.sin(1.3 * tphase + 4.188);
        double lr = 0.35;
        unknown lx = 2.4 * math.cos(tphase * 1.8);
        unknown ly = 1.8 + 0.8 * math.sin(tphase * 1.2);
        unknown lz = 2.4 * math.sin(tphase * 1.8);
        
        List<byte> frame = bytearray(width * height);
        double aspect = width / height;
        double fov = 1.25;
        for (long py = 0; py < height; py += 1) {
            long row_base = py * width;
            double sy = 1.0 - 2.0 * (py + 0.5) / height;
            for (long px = 0; px < width; px += 1) {
                double sx = (2.0 * (px + 0.5) / width - 1.0) * aspect;
                unknown rx = fwd_x + fov * (sx * right_x + sy * up_x);
                unknown ry = fwd_y + fov * (sx * right_y + sy * up_y);
                unknown rz = fwd_z + fov * (sx * right_z + sy * up_z);
                (dx, dy, dz) = normalize(rx, ry, rz);
                
                // Search for the nearest hit.
                double best_t = 1e9;
                long hit_kind = 0;
                double r = 0.0;
                double g = 0.0;
                double b = 0.0;
                
                // Floor plane y=-1.2
                if (dy < -1e-6) {
                    unknown tf = (-1.2 - cam_y) / dy;
                    if (tf > 1e-4 && tf < best_t) {
                        best_t = tf;
                        hit_kind = 1;
                    }
                }
                double t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65);
                if (t0 > 0.0 && t0 < best_t) {
                    best_t = t0;
                    hit_kind = 2;
                }
                double t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72);
                if (t1 > 0.0 && t1 < best_t) {
                    best_t = t1;
                    hit_kind = 3;
                }
                double t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58);
                if (t2 > 0.0 && t2 < best_t) {
                    best_t = t2;
                    hit_kind = 4;
                }
                if (hit_kind == 0) {
                    (r, g, b) = sky_color(dx, dy, dz, tphase);
                } else {
                    if (hit_kind == 1) {
                        unknown hx = cam_x + best_t * dx;
                        unknown hz = cam_z + best_t * dz;
                        long cx = System.Convert.ToInt64(math.floor(hx * 2.0));
                        long cz = System.Convert.ToInt64(math.floor(hz * 2.0));
                        long checker = ((cx + cz) % 2 == 0 ? 0 : 1);
                        double base_r = (checker == 0 ? 0.10 : 0.04);
                        double base_g = (checker == 0 ? 0.11 : 0.05);
                        double base_b = (checker == 0 ? 0.13 : 0.08);
                        // Emissive sphere contribution.
                        unknown lxv = lx - hx;
                        unknown lyv = ly - -1.2;
                        unknown lzv = lz - hz;
                        (ldx, ldy, ldz) = normalize(lxv, lyv, lzv);
                        unknown ndotl = max(ldy, 0.0);
                        unknown ldist2 = lxv * lxv + lyv * lyv + lzv * lzv;
                        unknown glow = 8.0 / (1.0 + ldist2);
                        r = base_r + 0.8 * glow + 0.20 * ndotl;
                        g = base_g + 0.5 * glow + 0.18 * ndotl;
                        b = base_b + 1.0 * glow + 0.24 * ndotl;
                    } else {
                        double cx = 0.0;
                        double cy = 0.0;
                        double cz = 0.0;
                        double rad = 1.0;
                        if (hit_kind == 2) {
                            cx = s0x;
                            cy = s0y;
                            cz = s0z;
                            rad = 0.65;
                        } else {
                            if (hit_kind == 3) {
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
                        unknown hx = cam_x + best_t * dx;
                        unknown hy = cam_y + best_t * dy;
                        unknown hz = cam_z + best_t * dz;
                        (nx, ny, nz) = normalize((hx - cx) / rad, (hy - cy) / rad, (hz - cz) / rad);
                        
                        // Simple glass shading (reflection + refraction + light highlights).
                        (rdx, rdy, rdz) = reflect(dx, dy, dz, nx, ny, nz);
                        (tdx, tdy, tdz) = refract(dx, dy, dz, nx, ny, nz, 1.0 / 1.45);
                        (sr, sg, sb) = sky_color(rdx, rdy, rdz, tphase);
                        (tr, tg, tb) = sky_color(tdx, tdy, tdz, tphase + 0.8);
                        unknown cosi = max(-(dx * nx + dy * ny + dz * nz), 0.0);
                        double fr = schlick(cosi, 0.04);
                        r = tr * (1.0 - fr) + sr * fr;
                        g = tg * (1.0 - fr) + sg * fr;
                        b = tb * (1.0 - fr) + sb * fr;
                        
                        unknown lxv = lx - hx;
                        unknown lyv = ly - hy;
                        unknown lzv = lz - hz;
                        (ldx, ldy, ldz) = normalize(lxv, lyv, lzv);
                        unknown ndotl = max(nx * ldx + ny * ldy + nz * ldz, 0.0);
                        (hvx, hvy, hvz) = normalize(ldx - dx, ldy - dy, ldz - dz);
                        unknown ndoth = max(nx * hvx + ny * hvy + nz * hvz, 0.0);
                        unknown spec = ndoth * ndoth;
                        spec = spec * spec;
                        spec = spec * spec;
                        spec = spec * spec;
                        unknown glow = 10.0 / (1.0 + lxv * lxv + lyv * lyv + lzv * lzv);
                        r += 0.20 * ndotl + 0.80 * spec + 0.45 * glow;
                        g += 0.18 * ndotl + 0.60 * spec + 0.35 * glow;
                        b += 0.26 * ndotl + 1.00 * spec + 0.65 * glow;
                        
                        // Slight tint variation per sphere.
                        if (hit_kind == 2) {
                            r *= 0.95;
                            g *= 1.05;
                            b *= 1.10;
                        } else {
                            if (hit_kind == 3) {
                                r *= 1.08;
                                g *= 0.98;
                                b *= 1.04;
                            } else {
                                r *= 1.02;
                                g *= 1.10;
                                b *= 0.95;
                            }
                        }
                    }
                }
                // Slightly stronger tone mapping.
                r = math.sqrt(clamp01(r));
                g = math.sqrt(clamp01(g));
                b = math.sqrt(clamp01(b));
                frame[System.Convert.ToInt32(row_base + px)] = quantize_332(r, g, b);
            }
        }
        return bytes(frame);
    }
    
    public static void run_16_glass_sculpture_chaos()
    {
        long width = 320;
        long height = 240;
        long frames_n = 72;
        string out_path = "sample/out/16_glass_sculpture_chaos.gif";
        
        unknown start = perf_counter();
        System.Collections.Generic.List<List<byte>> frames = new System.Collections.Generic.List<unknown>();
        for (long i = 0; i < frames_n; i += 1) {
            frames.Add(render_frame(width, height, i, frames_n));
        }
        save_gif(out_path, width, height, frames, palette_332());
        unknown elapsed = perf_counter() - start;
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "frames:", frames_n }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_16_glass_sculpture_chaos();
    }
}
