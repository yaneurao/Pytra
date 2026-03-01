import Foundation


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

func run_integer_grid_checksum(width: Int64, height: Int64, seed: Int64) -> Int64 {
    var mod_main: Int64 = Int64(2147483647)
    var mod_out: Int64 = Int64(1000000007)
    var acc: Int64 = (seed % mod_out)
    var y = __pytra_int(Int64(0))
    while (y < __pytra_int(height)) {
        var row_sum: Int64 = Int64(0)
        var x = __pytra_int(Int64(0))
        while (x < __pytra_int(width)) {
            var v: Int64 = ((((x * Int64(37)) + (y * Int64(73))) + seed) % mod_main)
            v = (((v * Int64(48271)) + Int64(1)) % mod_main)
            row_sum += (v % Int64(256))
            x += 1
        }
        acc = ((acc + (row_sum * (y + Int64(1)))) % mod_out)
        y += 1
    }
    return acc
}

func run_integer_benchmark() {
    var width: Int64 = Int64(7600)
    var height: Int64 = Int64(5000)
    var start: Double = __pytra_perf_counter()
    var checksum: Int64 = __pytra_int(run_integer_grid_checksum(width, height, Int64(123456789)))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("pixels:", (width * height))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

@main
struct Main {
    static func main() {
        run_integer_benchmark()
    }
}
