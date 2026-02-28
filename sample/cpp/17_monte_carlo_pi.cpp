#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/time.h"

// 17: Sample that scans a large grid using integer arithmetic only and computes a checksum.
// It avoids floating-point error effects, making cross-language comparisons easier.

int64 run_integer_grid_checksum(int64 width, int64 height, int64 seed) {
    int64 mod_main = 2147483647;
    int64 mod_out = 1000000007;
    int64 acc = seed % mod_out;
    
    for (int64 y = 0; y < height; ++y) {
        int64 row_sum = 0;
        for (int64 x = 0; x < width; ++x) {
            int64 v = (x * 37 + y * 73 + seed) % mod_main;
            v = (v * 48271 + 1) % mod_main;
            row_sum += v % 256;
        }
        acc = (acc + row_sum * (y + 1)) % mod_out;
    }
    return acc;
}

void run_integer_benchmark() {
    // Previous baseline: 2400 x 1600 (= 3,840,000 cells).
    // 7600 x 5000 (= 38,000,000 cells) is ~9.9x larger to make this case
    // meaningful in runtime benchmarks.
    int64 width = 7600;
    int64 height = 5000;
    
    float64 start = pytra::std::time::perf_counter();
    int64 checksum = run_integer_grid_checksum(width, height, 123456789);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    
    py_print("pixels:", width * height);
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_integer_benchmark();
    return 0;
}
