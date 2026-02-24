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
    let width: i64 = 2400;
    let height: i64 = 1600;
    
    let start: f64 = perf_counter();
    let checksum: i64 = run_integer_grid_checksum(width, height, 123456789);
    let elapsed: f64 = perf_counter() - start;
    
    println!("{:?}", ("pixels:", width * height));
    println!("{:?}", ("checksum:", checksum));
    println!("{:?}", ("elapsed_sec:", elapsed));
}

fn main() {
    run_integer_benchmark();
}
