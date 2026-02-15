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

bool is_large(int n)
{
    if ((n >= 10))
    {
        return true;
    }
    else
    {
        return false;
    }
}

int main()
{
    py_print(is_large(11));
    return 0;
}
