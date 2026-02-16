// このファイルは Python の `math` モジュール互換実装の本体です。

#include <cmath>

#include "cpp_module/math.h"

namespace pycs::cpp_module::math {

const double pi = 3.14159265358979323846;
const double e = 2.71828182845904523536;

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

double tan(double x) {
    return std::tan(x);
}

double log(double x) {
    return std::log(x);
}

double log10(double x) {
    return std::log10(x);
}

double fabs(double x) {
    return std::fabs(x);
}

double floor(double x) {
    return std::floor(x);
}

double ceil(double x) {
    return std::ceil(x);
}

double pow(double x, double y) {
    return std::pow(x, y);
}

}  // namespace pycs::cpp_module::math
