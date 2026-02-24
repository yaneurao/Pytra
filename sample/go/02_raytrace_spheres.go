using math;

public static class Program
{
    // 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
    // Dependencies are kept minimal (time only) for transpilation compatibility.
    
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
    
    public static double hit_sphere(double ox, double oy, double oz, double dx, double dy, double dz, double cx, double cy, double cz, double r)
    {
        double lx = ox - cx;
        double ly = oy - cy;
        double lz = oz - cz;
        
        double a = dx * dx + dy * dy + dz * dz;
        double b = 2.0 * (lx * dx + ly * dy + lz * dz);
        double c = lx * lx + ly * ly + lz * lz - r * r;
        
        double d = b * b - 4.0 * a * c;
        if (d < 0.0) {
            return -1.0;
        }
        double sd = math.sqrt(d);
        double t0 = (-b - sd) / (2.0 * a);
        double t1 = (-b + sd) / (2.0 * a);
        
        if (t0 > 0.001) {
            return t0;
        }
        if (t1 > 0.001) {
            return t1;
        }
        return -1.0;
    }
    
    public static List<byte> render(long width, long height, long aa)
    {
        List<byte> pixels = bytearray();
        
        // Camera origin
        double ox = 0.0;
        double oy = 0.0;
        double oz = -3.0;
        
        // Light direction (normalized)
        double lx = -0.4;
        double ly = 0.8;
        double lz = -0.45;
        for (long y = 0; y < height; y += 1) {
            for (long x = 0; x < width; x += 1) {
                long ar = 0;
                long ag = 0;
                long ab = 0;
                for (long ay = 0; ay < aa; ay += 1) {
                    for (long ax = 0; ax < aa; ax += 1) {
                        double fy = (y + (ay + 0.5) / aa) / (height - 1);
                        double fx = (x + (ax + 0.5) / aa) / (width - 1);
                        double sy = 1.0 - 2.0 * fy;
                        double sx = (2.0 * fx - 1.0) * (width / height);
                        
                        double dx = sx;
                        double dy = sy;
                        double dz = 1.0;
                        double inv_len = 1.0 / math.sqrt(dx * dx + dy * dy + dz * dz);
                        dx *= inv_len;
                        dy *= inv_len;
                        dz *= inv_len;
                        
                        double t_min = 1.0e30;
                        long hit_id = -1;
                        
                        double t = hit_sphere(ox, oy, oz, dx, dy, dz, -0.8, -0.2, 2.2, 0.8);
                        if (t > 0.0 && t < t_min) {
                            t_min = t;
                            hit_id = 0;
                        }
                        t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95);
                        if (t > 0.0 && t < t_min) {
                            t_min = t;
                            hit_id = 1;
                        }
                        t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, -1001.0, 3.0, 1000.0);
                        if (t > 0.0 && t < t_min) {
                            t_min = t;
                            hit_id = 2;
                        }
                        long r = 0;
                        long g = 0;
                        long b = 0;
                        
                        if (hit_id >= 0) {
                            double px = ox + dx * t_min;
                            double py = oy + dy * t_min;
                            double pz = oz + dz * t_min;
                            
                            double nx = 0.0;
                            double ny = 0.0;
                            double nz = 0.0;
                            
                            if (hit_id == 0) {
                                nx = (px + 0.8) / 0.8;
                                ny = (py + 0.2) / 0.8;
                                nz = (pz - 2.2) / 0.8;
                            } else {
                                if (hit_id == 1) {
                                    nx = (px - 0.9) / 0.95;
                                    ny = (py - 0.1) / 0.95;
                                    nz = (pz - 2.9) / 0.95;
                                } else {
                                    nx = 0.0;
                                    ny = 1.0;
                                    nz = 0.0;
                                }
                            }
                            double diff = nx * -lx + ny * -ly + nz * -lz;
                            diff = clamp01(diff);
                            
                            double base_r = 0.0;
                            double base_g = 0.0;
                            double base_b = 0.0;
                            
                            if (hit_id == 0) {
                                base_r = 0.95;
                                base_g = 0.35;
                                base_b = 0.25;
                            } else {
                                if (hit_id == 1) {
                                    base_r = 0.25;
                                    base_g = 0.55;
                                    base_b = 0.95;
                                } else {
                                    long checker = System.Convert.ToInt64((px + 50.0) * 0.8) + System.Convert.ToInt64((pz + 50.0) * 0.8);
                                    if (checker % 2 == 0) {
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
                            double shade = 0.12 + 0.88 * diff;
                            r = System.Convert.ToInt64(255.0 * clamp01(base_r * shade));
                            g = System.Convert.ToInt64(255.0 * clamp01(base_g * shade));
                            b = System.Convert.ToInt64(255.0 * clamp01(base_b * shade));
                        } else {
                            double tsky = 0.5 * (dy + 1.0);
                            r = System.Convert.ToInt64(255.0 * (0.65 + 0.20 * tsky));
                            g = System.Convert.ToInt64(255.0 * (0.75 + 0.18 * tsky));
                            b = System.Convert.ToInt64(255.0 * (0.90 + 0.08 * tsky));
                        }
                        ar += r;
                        ag += g;
                        ab += b;
                    }
                }
                long samples = aa * aa;
                pixels.Add(System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(ar) / System.Convert.ToDouble(samples))));
                pixels.Add(System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(ag) / System.Convert.ToDouble(samples))));
                pixels.Add(System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(ab) / System.Convert.ToDouble(samples))));
            }
        }
        return pixels;
    }
    
    public static void run_raytrace()
    {
        long width = 1600;
        long height = 900;
        long aa = 2;
        string out_path = "sample/out/02_raytrace_spheres.png";
        
        double start = perf_counter();
        List<byte> pixels = render(width, height, aa);
        png.write_rgb_png(out_path, width, height, pixels);
        double elapsed = perf_counter() - start;
        
        System.Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
        System.Console.WriteLine(string.Join(" ", new object[] { "size:", width, "x", height }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_raytrace();
    }
}
