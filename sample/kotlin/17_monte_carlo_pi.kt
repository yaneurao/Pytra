import kotlin.math.*


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

fun run_integer_grid_checksum(width: Long, height: Long, seed: Long): Long {
    var mod_main: Long = 2147483647L
    var mod_out: Long = 1000000007L
    var acc: Long = (seed % mod_out)
    var y = __pytra_int(0L)
    while (y < __pytra_int(height)) {
        var row_sum: Long = 0L
        var x = __pytra_int(0L)
        while (x < __pytra_int(width)) {
            var v: Long = ((((x * 37L) + (y * 73L)) + seed) % mod_main)
            v = (((v * 48271L) + 1L) % mod_main)
            row_sum += (v % 256L)
            x += 1L
        }
        acc = ((acc + (row_sum * (y + 1L))) % mod_out)
        y += 1L
    }
    return acc
}

fun run_integer_benchmark() {
    var width: Long = 7600L
    var height: Long = 5000L
    var start: Double = __pytra_perf_counter()
    var checksum: Long = __pytra_int(run_integer_grid_checksum(width, height, 123456789L))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("pixels:", (width * height))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_integer_benchmark()
}
