// このファイルは Python の `math` モジュール互換実装の本体です。

#include <cmath>

#include "cpp_module/math.h"

namespace pycs::cpp_module::math {

const double pi = 3.14159265358979323846;

double sqrt(double x) {
    return std::sqrt(x);
}

double sin(double x) {
    return std::sin(x);
}

double cos(double x) {
    return std::cos(x);
}

double exp(double x) {
    return std::exp(x);
}

}  // namespace pycs::cpp_module::math
