using System;
using System.Collections.Generic;
using System.Linq;
using Pytra.CsModule;

public static class Program
{
    // 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
    // It avoids floating-point error effects, making cross-language comparisons easier.
    
    public static long run_integer_grid_checksum(long width, long height, long seed)
    {
        long mod_main = 2147483647;
        long mod_out = 1000000007;
        long acc = seed % mod_out;
        
        long y = 0;
        for (y = 0; y < height; y += 1) {
            long row_sum = 0;
            long x = 0;
            for (x = 0; x < width; x += 1) {
                long v = (x * 37 + y * 73 + seed) % mod_main;
                v = (v * 48271 + 1) % mod_main;
                row_sum += v % 256;
            }
            acc = (acc + row_sum * (y + 1)) % mod_out;
        }
        return acc;
    }
    
    public static void run_integer_benchmark()
    {
        // Previous baseline: 2400 x 1600 (= 3,840,000 cells).
        // 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
        // meaningful in runtime benchmarks.
        long width = 7600;
        long height = 5000;
        
        double start = Pytra.CsModule.time.perf_counter();
        long checksum = run_integer_grid_checksum(width, height, 123456789);
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        
        System.Console.WriteLine(string.Join(" ", new object[] { "pixels:", width * height }));
        System.Console.WriteLine(string.Join(" ", new object[] { "checksum:", checksum }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void Main(string[] args)
    {
            run_integer_benchmark();
    }
}
