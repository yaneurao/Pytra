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

int fib(int n)
{
    if ((n <= 1))
    {
        return n;
    }
    return (fib((n - 1)) + fib((n - 2)));
}

int main()
{
    py_print(fib(10));
    return 0;
}
