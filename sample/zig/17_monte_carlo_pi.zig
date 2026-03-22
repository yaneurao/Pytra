const std = @import("std");
const pytra = @import("built_in/py_runtime.zig");
const time = @import("std/time.zig");
const perf_counter = time.perf_counter;

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

fn run_integer_grid_checksum(width: i64, height: i64, seed: i64) i64 {
    const mod_main: i64 = 2147483647;
    const mod_out: i64 = 1000000007;
    var acc: i64 = @mod(seed, mod_out);
    
    var y: i64 = 0;
    while (y < height) : (y += 1) {
        var row_sum: i64 = 0;
        var x: i64 = 0;
        while (x < width) : (x += 1) {
            var v: i64 = @mod((((x * 37) + (y * 73)) + seed), mod_main);
            v = @mod(((v * 48271) + 1), mod_main);
            row_sum += @mod(v, 256);
        }
        acc = @mod((acc + (row_sum * (y + 1))), mod_out);
    }
    return acc;
}

fn run_integer_benchmark() void {
    // Previous baseline: 2400 x 1600 (= 3,840,000 cells).
    // 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
    // meaningful in runtime benchmarks.
    const width: i64 = 7600;
    const height: i64 = 5000;
    
    const start: f64 = pytra.perf_counter();
    const checksum: i64 = run_integer_grid_checksum(width, height, 123456789);
    const elapsed: f64 = (pytra.perf_counter() - start);
    
    pytra.print2("pixels:", (width * height));
    pytra.print2("checksum:", checksum);
    pytra.print2("elapsed_sec:", elapsed);
}

pub fn main() void {
    run_integer_benchmark();
}
