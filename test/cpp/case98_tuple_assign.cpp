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

int swap_sum_98(int a, int b)
{
    int x = a;
    int y = b;
    auto _tmp_tuple = std::make_tuple(y, x);
    x = std::get<0>(_tmp_tuple);
    y = std::get<1>(_tmp_tuple);
    return (x + y);
}

int main()
{
    py_print(swap_sum_98(10, 20));
    return 0;
}
