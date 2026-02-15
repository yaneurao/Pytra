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

int maybe_fail_39(bool flag)
{
    try
    {
        if (flag)
        {
            throw std::runtime_error(py_to_string("fail-39"));
        }
        return 10;
    }
    catch (const std::exception& ex)
    {
        return 20;
    }
    // finally is not directly supported in C++; emitted as plain block
    {
    }
}

int main()
{
    py_print(maybe_fail_39(true));
    return 0;
}
