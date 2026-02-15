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

int calc_27(const vector<int>& values)
{
    int total = 0;
    for (const auto& v : values)
    {
        if (((v % 2) == 0))
        {
            total = (total + v);
        }
        else
        {
            total = (total + (v * 2));
        }
    }
    return total;
}

int main()
{
    py_print(calc_27({1, 2, 3, 4}));
    return 0;
}
