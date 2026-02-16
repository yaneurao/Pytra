#include "cpp_module/gc.h"
#include "cpp_module/py_runtime_modules.h"
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

auto py_main()
{
    int8_t i = 1;
    py_print((i * 2));
}

int main()
{
    py_main();
    return 0;
}
