#include "cpp_module/py_runtime.h"

void __pytra_main() {
    py_print(pycs::cpp_module::math::fabs(pycs::cpp_module::math::tan(0.0)) < 1e-12);
    py_print(pycs::cpp_module::math::fabs(pycs::cpp_module::math::log(pycs::cpp_module::math::exp(1.0)) - 1.0) < 1e-12);
    py_print(py_to_int64(pycs::cpp_module::math::log10(1000.0)));
    py_print(py_to_int64(pycs::cpp_module::math::fabs(-3.5) * 10.0));
    py_print(py_to_int64(pycs::cpp_module::math::ceil(2.1)));
    py_print(py_to_int64(pycs::cpp_module::math::pow(2.0, 5.0)));
}

int main() {
    __pytra_main();
    return 0;
}
