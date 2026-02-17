#include "cpp_module/gc.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

long long run_integer_grid_checksum(long long width, long long height, long long seed)
{
    long long mod_main = 2147483647;
    long long mod_out = 1000000007;
    long long acc = py_mod(seed, mod_out);
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = height;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto y = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (y < __pytra_range_stop_2) : (y > __pytra_range_stop_2); y += __pytra_range_step_3)
    {
        long long row_sum = 0;
        auto __pytra_range_start_4 = 0;
        auto __pytra_range_stop_5 = width;
        auto __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
        for (auto x = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (x < __pytra_range_stop_5) : (x > __pytra_range_stop_5); x += __pytra_range_step_6)
        {
            long long v = py_mod((((x * 37) + (y * 73)) + seed), mod_main);
            v = py_mod(((v * 48271) + 1), mod_main);
            row_sum = (row_sum + py_mod(v, 256));
        }
        acc = py_mod((acc + (row_sum * (y + 1))), mod_out);
    }
    return acc;
}

void run_integer_benchmark()
{
    long long width = 2400;
    long long height = 1600;
    double start = perf_counter();
    long long checksum = run_integer_grid_checksum(width, height, 123456789);
    double elapsed = (perf_counter() - start);
    py_print("pixels:", (width * height));
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_integer_benchmark();
    return 0;
}
