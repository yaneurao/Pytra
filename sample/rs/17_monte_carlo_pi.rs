mod py_runtime;
pub use crate::py_runtime::{math, pytra, time};
use crate::py_runtime::*;

use crate::time::perf_counter;

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

fn run_integer_grid_checksum(width: i64, height: i64, seed: i64) -> i64 {
    let mod_main: i64 = 2147483647;
    let mod_out: i64 = 1000000007;
    let mut acc: i64 = seed % mod_out;
    
    let mut y: i64 = 0;
    while y < height {
        let mut row_sum: i64 = 0;
        let mut x: i64 = 0;
        while x < width {
            let mut v: i64 = (x * 37 + y * 73 + seed) % mod_main;
            v = (v * 48271 + 1) % mod_main;
            row_sum += v % 256;
            x += 1;
        }
        acc = (acc + row_sum * (y + 1)) % mod_out;
        y += 1;
    }
    return acc;
}

fn run_integer_benchmark() {
    // Previous baseline: 2400 x 1600 (= 3,840,000 cells).
    // 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
    // meaningful in runtime benchmarks.
    let width: i64 = 7600;
    let height: i64 = 5000;
    
    let start: f64 = perf_counter();
    let checksum: i64 = run_integer_grid_checksum(width, height, 123456789);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{} {}", ("pixels:").to_string(), width * height);
    println!("{} {}", ("checksum:").to_string(), checksum);
    println!("{} {}", ("elapsed_sec:").to_string(), elapsed);
}

fn main() {
    run_integer_benchmark();
}
