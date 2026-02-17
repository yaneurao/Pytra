#include "cpp_module/py_runtime.h"

void __pytra_main() {
    py_print(py_math::fabs(py_math::tan(0.0)) < 1e-12);
    py_print(py_math::fabs(py_math::log(py_math::exp(1.0)) - 1.0) < 1e-12);
    py_print(py_to_int64(py_math::log10(1000.0)));
    py_print(py_to_int64(py_math::fabs(-3.5) * 10.0));
    py_print(py_to_int64(py_math::ceil(2.1)));
    py_print(py_to_int64(py_math::pow(2.0, 5.0)));
}

int main() {
    __pytra_main();
    return 0;
}
