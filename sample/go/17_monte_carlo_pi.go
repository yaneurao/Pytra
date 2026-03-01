package main


// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

func run_integer_grid_checksum(width int64, height int64, seed int64) int64 {
    var mod_main int64 = int64(2147483647)
    var mod_out int64 = int64(1000000007)
    var acc int64 = (seed % mod_out)
    for y := int64(0); y < height; y += 1 {
        var row_sum int64 = int64(0)
        for x := int64(0); x < width; x += 1 {
            var v int64 = ((((x * int64(37)) + (y * int64(73))) + seed) % mod_main)
            v = (((v * int64(48271)) + int64(1)) % mod_main)
            row_sum += (v % int64(256))
        }
        acc = ((acc + (row_sum * (y + int64(1)))) % mod_out)
    }
    return acc
}

func run_integer_benchmark() {
    var width int64 = int64(7600)
    var height int64 = int64(5000)
    var start float64 = __pytra_perf_counter()
    var checksum int64 = run_integer_grid_checksum(width, height, int64(123456789))
    var elapsed float64 = (__pytra_perf_counter() - start)
    __pytra_print("pixels:", (width * height))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

func main() {
    run_integer_benchmark()
}
