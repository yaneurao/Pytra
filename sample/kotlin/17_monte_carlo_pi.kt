// このファイルは EAST ベース Kotlin プレビュー出力です。
// TODO: 専用 KotlinEmitter 実装へ段階移行する。
fun main() {
    /*
    using System;
    using System.Collections.Generic;
    using System.Linq;
    
    public static class Program
    {
        // 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
        // It avoids floating-point error effects, making cross-language comparisons easier.
        
        public static long run_integer_grid_checksum(long width, long height, long seed)
        {
            long mod_main = 2147483647;
            long mod_out = 1000000007;
            long acc = (seed % mod_out);
            
            for (long y = 0; y < height; y += 1) {
                long row_sum = 0;
                for (long x = 0; x < width; x += 1) {
                    long v = (((((x * 37) + (y * 73)) + seed)) % mod_main);
                    v = ((((v * 48271) + 1)) % mod_main);
                    row_sum += (v % 256);
                }
                acc = (((acc + (row_sum * ((y + 1))))) % mod_out);
            }
            return acc;
        }
        
        public static void run_integer_benchmark()
        {
            long width = 2400;
            long height = 1600;
            
            double start = perf_counter();
            long checksum = run_integer_grid_checksum(width, height, 123456789);
            double elapsed = (perf_counter() - start);
            
            Console.WriteLine(string.Join(" ", new object[] { "pixels:", (width * height) }));
            Console.WriteLine(string.Join(" ", new object[] { "checksum:", checksum }));
            Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
        }
        
        public static void Main(string[] args)
        {
                run_integer_benchmark();
        }
    }
    */
}
