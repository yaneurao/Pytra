import kotlin.math.*


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

fun run_integer_grid_checksum(width: Long, height: Long, seed: Long): Long {
    var mod_main: Long = __pytra_int(2147483647L)
    var mod_out: Long = __pytra_int(1000000007L)
    var acc: Long = __pytra_int((__pytra_int(seed) % __pytra_int(mod_out)))
    val __step_0 = __pytra_int(1L)
    var y = __pytra_int(0L)
    while ((__step_0 >= 0L && y < __pytra_int(height)) || (__step_0 < 0L && y > __pytra_int(height))) {
        var row_sum: Long = __pytra_int(0L)
        val __step_1 = __pytra_int(1L)
        var x = __pytra_int(0L)
        while ((__step_1 >= 0L && x < __pytra_int(width)) || (__step_1 < 0L && x > __pytra_int(width))) {
            var v: Long = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(37L))) + __pytra_int((__pytra_int(y) * __pytra_int(73L))))) + __pytra_int(seed))) % __pytra_int(mod_main)))
            v = __pytra_int((__pytra_int((__pytra_int((__pytra_int(v) * __pytra_int(48271L))) + __pytra_int(1L))) % __pytra_int(mod_main)))
            row_sum += (__pytra_int(v) % __pytra_int(256L))
            x += __step_1
        }
        acc = __pytra_int((__pytra_int((__pytra_int(acc) + __pytra_int((__pytra_int(row_sum) * __pytra_int((__pytra_int(y) + __pytra_int(1L))))))) % __pytra_int(mod_out)))
        y += __step_0
    }
    return __pytra_int(acc)
}

fun run_integer_benchmark() {
    var width: Long = __pytra_int(7600L)
    var height: Long = __pytra_int(5000L)
    var start: Double = __pytra_float(__pytra_perf_counter())
    var checksum: Long = __pytra_int(run_integer_grid_checksum(width, height, 123456789L))
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("pixels:", (__pytra_int(width) * __pytra_int(height)))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

fun main(args: Array<String>) {
    run_integer_benchmark()
}
