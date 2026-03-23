final class _17_monte_carlo_pi {
    private _17_monte_carlo_pi() {
    }


    // 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
    // It avoids floating-point error effects, making cross-language comparisons easier.

    public static long run_integer_grid_checksum(long width, long height, long seed) {
        long mod_main = 2147483647L;
        long mod_out = 1000000007L;
        long acc = seed % mod_out;
        for (long y = 0L; y < height; y += 1L) {
            long row_sum = 0L;
            for (long x = 0L; x < width; x += 1L) {
                long v = (x * 37L + y * 73L + seed) % mod_main;
                v = (v * 48271L + 1L) % mod_main;
                row_sum += v % 256L;
            }
            acc = (acc + row_sum * (y + 1L)) % mod_out;
        }
        return acc;
    }

    public static void run_integer_benchmark() {
        long width = 7600L;
        long height = 5000L;
        String out_path = "sample/out/17_monte_carlo_pi.txt";
        double start = time.perf_counter();
        long checksum = run_integer_grid_checksum(width, height, 123456789L);
        double elapsed = time.perf_counter() - start;
        String result = "pixels:" + String.valueOf(width * height) + "\nchecksum:" + String.valueOf(checksum) + "\n";
        pathlib.Path p = new pathlib.Path(out_path);
        p.write_text(result, "utf-8");
        System.out.println(String.valueOf("pixels:") + " " + String.valueOf(width * height));
        System.out.println(String.valueOf("checksum:") + " " + String.valueOf(checksum));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void _case_main() {
        run_integer_benchmark();
    }
}
