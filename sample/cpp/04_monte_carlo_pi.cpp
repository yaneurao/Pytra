#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
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

long long lcg_next(long long state)
{
    return (((1664525LL * state) + 1013904223LL) % 4294967296LL);
}

double run_pi_trial(long long total_samples, long long seed)
{
    long long inside = 0LL;
    long long state = seed;
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = total_samples;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto _ = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (_ < __pytra_range_stop_2) : (_ > __pytra_range_stop_2); _ += __pytra_range_step_3)
    {
        state = lcg_next(state);
        double x = py_div(state, 4294967296.0);
        state = lcg_next(state);
        double y = py_div(state, 4294967296.0);
        double dx = (x - 0.5);
        double dy = (y - 0.5);
        if ((((dx * dx) + (dy * dy)) <= 0.25))
        {
            inside = (inside + 1LL);
        }
    }
    return py_div((4.0 * inside), total_samples);
}

void run_monte_carlo_pi()
{
    long long samples = 18000000LL;
    long long seed = 123456789LL;
    double start = perf_counter();
    double pi_est = run_pi_trial(samples, seed);
    double elapsed = (perf_counter() - start);
    py_print("samples:", samples);
    py_print("pi_estimate:", pi_est);
    py_print("elapsed_sec:", elapsed);
}

int main()
{
    run_monte_carlo_pi();
    return 0;
}
