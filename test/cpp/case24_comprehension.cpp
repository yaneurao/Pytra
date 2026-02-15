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

int comp_like_24(int x)
{
    vector<int> values = /* comprehension */ {};
    return (x + 1);
}

int main()
{
    py_print(comp_like_24(5));
    return 0;
}
