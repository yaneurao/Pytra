// Auto-generated Java native source from EAST3.
public final class Pytra_17_monte_carlo_pi {
    private Pytra_17_monte_carlo_pi() {
    }


    // 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
    // It avoids floating-point error effects, making cross-language comparisons easier.

    public static long run_integer_grid_checksum(long width, long height, long seed) {
        long mod_main = 2147483647L;
        long mod_out = 1000000007L;
        long acc = (seed % mod_out);
        long __step_0 = 1L;
        for (long y = 0L; (__step_0 >= 0L) ? (y < height) : (y > height); y += __step_0) {
            long row_sum = 0L;
            long __step_1 = 1L;
            for (long x = 0L; (__step_1 >= 0L) ? (x < width) : (x > width); x += __step_1) {
                long v = ((((x * 37L) + (y * 73L)) + seed) % mod_main);
                v = (((v * 48271L) + 1L) % mod_main);
                row_sum += (v % 256L);
            }
            acc = ((acc + (row_sum * (y + 1L))) % mod_out);
        }
        return acc;
    }

    public static void run_integer_benchmark() {
        long width = 7600L;
        long height = 5000L;
        double start = (System.nanoTime() / 1000000000.0);
        long checksum = run_integer_grid_checksum(width, height, 123456789L);
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("pixels:") + " " + String.valueOf((width * height)));
        System.out.println(String.valueOf("checksum:") + " " + String.valueOf(checksum));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void main(String[] args) {
        run_integer_benchmark();
    }
}
