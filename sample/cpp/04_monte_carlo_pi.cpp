#include "cpp_module/py_runtime.h"

// 04: 整数演算のみで大きなグリッドを走査し、チェックサムを計算するサンプルです。
// 浮動小数点誤差の影響を避け、言語間で比較しやすいベンチマークにします。

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
    int64 width = 2400;
    int64 height = 1600;
    
    float64 start = perf_counter();
    int64 checksum = run_integer_grid_checksum(width, height, 123456789);
    float64 elapsed = perf_counter() - start;
    
    py_print("pixels:", width * height);
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_integer_benchmark();
    return 0;
}
