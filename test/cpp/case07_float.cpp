#include "cpp_module/gc.h"
#include "cpp_module/py_runtime.h"
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

double half(double x)
{
    return (x / 2.0);
}

int main()
{
    py_print(half(5.0));
    return 0;
}
