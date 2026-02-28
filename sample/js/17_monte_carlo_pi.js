import { perf_counter } from "./pytra/std/time.js";

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

function run_integer_grid_checksum(width, height, seed) {
    let mod_main = 2147483647;
    let mod_out = 1000000007;
    let acc = seed % mod_out;
    
    const __start_1 = 0;
    for (let y = __start_1; y < height; y += 1) {
        let row_sum = 0;
        const __start_2 = 0;
        for (let x = __start_2; x < width; x += 1) {
            let v = (x * 37 + y * 73 + seed) % mod_main;
            v = (v * 48271 + 1) % mod_main;
            row_sum += v % 256;
        }
        acc = (acc + row_sum * (y + 1)) % mod_out;
    }
    return acc;
}

function run_integer_benchmark() {
    // Previous baseline: 2400 x 1600 (= 3,840,000 cells).
    // 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
    // meaningful in runtime benchmarks.
    let width = 7600;
    let height = 5000;
    
    let start = perf_counter();
    let checksum = run_integer_grid_checksum(width, height, 123456789);
    let elapsed = perf_counter() - start;
    
    console.log("pixels:", width * height);
    console.log("checksum:", checksum);
    console.log("elapsed_sec:", elapsed);
}

run_integer_benchmark();
