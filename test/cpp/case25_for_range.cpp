#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
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

int sum_range_29(int n)
{
    int total = 0;
    auto __range_start_i = 0;
    auto __range_stop_i = n;
    auto __range_step_i = 1;
    if (__range_step_i == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __range_start_i; (__range_step_i > 0) ? (i < __range_stop_i) : (i > __range_stop_i); i += __range_step_i)
    {
        total = (total + i);
    }
    return total;
}

int main()
{
    py_print(sum_range_29(5));
    return 0;
}
