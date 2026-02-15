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

bool has_key_33(const string& k)
{
    unordered_map<string, int> d = {{ "a", 1 }, { "b", 2 }};
    if (py_in(k, d))
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
    py_print(has_key_33("a"));
    return 0;
}
