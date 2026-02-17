#include "cpp_module/gc.h"
#include "cpp_module/math.h"
#include "cpp_module/py_runtime.h"
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

void py_main()
{
    py_print((pycs::cpp_module::math::fabs(pycs::cpp_module::math::tan(0.0)) < 1e-12));
    py_print((pycs::cpp_module::math::fabs((pycs::cpp_module::math::log(pycs::cpp_module::math::exp(1.0)) - 1.0)) < 1e-12));
    py_print(py_int(pycs::cpp_module::math::log10(1000.0)));
    py_print(py_int((pycs::cpp_module::math::fabs((-3.5)) * 10.0)));
    py_print(py_int(pycs::cpp_module::math::ceil(2.1)));
    py_print(py_int(pycs::cpp_module::math::pow(2.0, 5.0)));
}

int main()
{
    py_main();
    return 0;
}
