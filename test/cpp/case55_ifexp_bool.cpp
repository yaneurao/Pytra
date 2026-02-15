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

int pick_55(int a, int b, bool flag)
{
    int c = ((flag && (a > b)) ? a : b);
    return c;
}

int main()
{
    py_print(pick_55(10, 3, true));
    return 0;
}
