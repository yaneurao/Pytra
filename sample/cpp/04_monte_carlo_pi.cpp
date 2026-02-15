#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
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

int lcg_next(int state)
{
    return (((1664525 * state) + 1013904223) % 4294967296);
}

double run_pi_trial(int total_samples, int seed)
{
    int inside = 0;
    int state = seed;
    int i = 0;
    while ((i < total_samples))
    {
        state = lcg_next(state);
        double x = ((state * 1.0) / 4294967296.0);
        state = lcg_next(state);
        double y = ((state * 1.0) / 4294967296.0);
        double dx = (x - 0.5);
        double dy = (y - 0.5);
        if ((((dx * dx) + (dy * dy)) <= 0.25))
        {
            inside = (inside + 1);
        }
        i = (i + 1);
    }
    return ((4.0 * (inside * 1.0)) / (total_samples * 1.0));
}

void run_monte_carlo_pi()
{
    int samples = 18000000;
    int seed = 123456789;
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
