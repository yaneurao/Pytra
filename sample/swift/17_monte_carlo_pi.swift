import Foundation


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

func run_integer_grid_checksum(width: Int64, height: Int64, seed: Int64) -> Int64 {
    var mod_main: Int64 = __pytra_int(Int64(2147483647))
    var mod_out: Int64 = __pytra_int(Int64(1000000007))
    var acc: Int64 = __pytra_int((__pytra_int(seed) % __pytra_int(mod_out)))
    let __step_0 = __pytra_int(Int64(1))
    var y = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height))) {
        var row_sum: Int64 = __pytra_int(Int64(0))
        let __step_1 = __pytra_int(Int64(1))
        var x = __pytra_int(Int64(0))
        while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width))) {
            var v: Int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(Int64(37)))) + __pytra_int((__pytra_int(y) * __pytra_int(Int64(73)))))) + __pytra_int(seed))) % __pytra_int(mod_main)))
            v = __pytra_int((__pytra_int((__pytra_int((__pytra_int(v) * __pytra_int(Int64(48271)))) + __pytra_int(Int64(1)))) % __pytra_int(mod_main)))
            row_sum += (__pytra_int(v) % __pytra_int(Int64(256)))
            x += __step_1
        }
        acc = __pytra_int((__pytra_int((__pytra_int(acc) + __pytra_int((__pytra_int(row_sum) * __pytra_int((__pytra_int(y) + __pytra_int(Int64(1)))))))) % __pytra_int(mod_out)))
        y += __step_0
    }
    return acc
}

func run_integer_benchmark() {
    var width: Int64 = __pytra_int(Int64(7600))
    var height: Int64 = __pytra_int(Int64(5000))
    var start: Double = __pytra_float(__pytra_perf_counter())
    var checksum: Int64 = __pytra_int(run_integer_grid_checksum(width, height, Int64(123456789)))
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("pixels:", (__pytra_int(width) * __pytra_int(height)))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_integer_benchmark()
    }
}
