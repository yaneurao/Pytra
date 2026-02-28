// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "math"
)

// Runtime helpers are provided by py_runtime.go in the same package.
var _ = math.Pi


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

func run_integer_grid_checksum(width int64, height int64, seed int64) int64 {
    var mod_main int64 = __pytra_int(int64(2147483647))
    var mod_out int64 = __pytra_int(int64(1000000007))
    var acc int64 = __pytra_int((__pytra_int(seed) % __pytra_int(mod_out)))
    __step_0 := __pytra_int(int64(1))
    for y := __pytra_int(int64(0)); (__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)); y += __step_0 {
        var row_sum int64 = __pytra_int(int64(0))
        __step_1 := __pytra_int(int64(1))
        for x := __pytra_int(int64(0)); (__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)); x += __step_1 {
            var v int64 = __pytra_int((__pytra_int((__pytra_int((__pytra_int((__pytra_int(x) * __pytra_int(int64(37)))) + __pytra_int((__pytra_int(y) * __pytra_int(int64(73)))))) + __pytra_int(seed))) % __pytra_int(mod_main)))
            v = __pytra_int((__pytra_int((__pytra_int((__pytra_int(v) * __pytra_int(int64(48271)))) + __pytra_int(int64(1)))) % __pytra_int(mod_main)))
            row_sum += (__pytra_int(v) % __pytra_int(int64(256)))
        }
        acc = __pytra_int((__pytra_int((__pytra_int(acc) + __pytra_int((__pytra_int(row_sum) * __pytra_int((__pytra_int(y) + __pytra_int(int64(1)))))))) % __pytra_int(mod_out)))
    }
    return __pytra_int(acc)
}

func run_integer_benchmark() {
    var width int64 = __pytra_int(int64(7600))
    var height int64 = __pytra_int(int64(5000))
    var start float64 = __pytra_float(__pytra_perf_counter())
    var checksum int64 = __pytra_int(run_integer_grid_checksum(width, height, int64(123456789)))
    var elapsed float64 = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
    __pytra_print("pixels:", (__pytra_int(width) * __pytra_int(height)))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_integer_benchmark()
}
