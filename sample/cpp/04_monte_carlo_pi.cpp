#include "cpp_module/py_runtime.h"


int64 run_integer_grid_checksum(int64 width, int64 height, int64 seed) {
    int64 row_sum;
    int64 v;
    
    int64 mod_main = 2147483647;
    int64 mod_out = 1000000007;
    int64 acc = seed % mod_out;
    
    for (int64 y = 0; y < height; ++y) {
        row_sum = 0;
        for (int64 x = 0; x < width; ++x) {
            v = (x * 37 + y * 73 + seed) % mod_main;
            v = (v * 48271 + 1) % mod_main;
            row_sum += v % 256;
        }
        acc = (acc + row_sum * (y + 1)) % mod_out;
    }
    
    return acc;
}

void run_integer_benchmark() {
    int64 width = 2400;
    int64 height = 1600;
    
    float64 start = perf_counter();
    int64 checksum = run_integer_grid_checksum(width, height, 123456789);
    float64 elapsed = perf_counter() - start;
    
    py_print("pixels:", width * height);
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

int main() {
    run_integer_benchmark();
    return 0;
}
