// このファイルは EAST ベース Java プレビュー出力です。
// TODO: 専用 JavaEmitter 実装へ段階移行する。
public final class Main {
    public static void main(String[] args) {
        /*
        using System;
        using System.Collections.Generic;
        using System.Linq;
        
        public static class Program
        {
            // 04: Sample that renders an orbit-trap Julia set and writes a PNG image.
            
            public static List<byte> render_orbit_trap_julia(long width, long height, long max_iter, double cx, double cy)
            {
                List<byte> pixels = bytearray();
                
                for (long y = 0; y < height; y += 1) {
                    double zy0 = ((-1.3) + (2.6 * ((y / ((height - 1))))));
                    for (long x = 0; x < width; x += 1) {
                        double zx = ((-1.9) + (3.8 * ((x / ((width - 1))))));
                        double zy = zy0;
                        
                        double trap = 1.0e9;
                        long i = 0;
                        while (i < max_iter) {
                            double ax = zx;
                            if (ax < 0.0) {
                                ax = (-ax);
                            }
                            double ay = zy;
                            if (ay < 0.0) {
                                ay = (-ay);
                            }
                            double dxy = (zx - zy);
                            if (dxy < 0.0) {
                                dxy = (-dxy);
                            }
                            if (ax < trap) {
                                trap = ax;
                            }
                            if (ay < trap) {
                                trap = ay;
                            }
                            if (dxy < trap) {
                                trap = dxy;
                            }
                            double zx2 = (zx * zx);
                            double zy2 = (zy * zy);
                            if ((zx2 + zy2) > 4.0) {
                                py_break;
                            }
                            zy = (((2.0 * zx) * zy) + cy);
                            zx = ((zx2 - zy2) + cx);
                            i += 1;
                        }
                        long r = 0;
                        long g = 0;
                        long b = 0;
                        if (i >= max_iter) {
                            r = 0;
                            g = 0;
                            b = 0;
                        } else {
                            double trap_scaled = (trap * 3.2);
                            if (trap_scaled > 1.0) {
                                trap_scaled = 1.0;
                            }
                            if (trap_scaled < 0.0) {
                                trap_scaled = 0.0;
                            }
                            double t = (i / max_iter);
                            long tone = Convert.ToInt64((255.0 * ((1.0 - trap_scaled))));
                            r = Convert.ToInt64((tone * ((0.35 + (0.65 * t)))));
                            g = Convert.ToInt64((tone * ((0.15 + (0.85 * ((1.0 - t)))))));
                            b = Convert.ToInt64((255.0 * ((0.25 + (0.75 * t)))));
                            if (r > 255) {
                                r = 255;
                            }
                            if (g > 255) {
                                g = 255;
                            }
                            if (b > 255) {
                                b = 255;
                            }
                        }
                        pixels.Add(r);
                        pixels.Add(g);
                        pixels.Add(b);
                    }
                }
                return pixels;
            }
            
            public static void run_04_orbit_trap_julia()
            {
                long width = 1920;
                long height = 1080;
                long max_iter = 1400;
                string out_path = "sample/out/04_orbit_trap_julia.png";
                
                double start = perf_counter();
                List<byte> pixels = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889);
                png.write_rgb_png(out_path, width, height, pixels);
                double elapsed = (perf_counter() - start);
                
                Console.WriteLine(string.Join(" ", new object[] { "output:", out_path }));
                Console.WriteLine(string.Join(" ", new object[] { "size:", width, "x", height }));
                Console.WriteLine(string.Join(" ", new object[] { "max_iter:", max_iter }));
                Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
            }
            
            public static void Main(string[] args)
            {
                    run_04_orbit_trap_julia();
            }
        }
        */
    }
}
