#include "runtime/cpp/core/built_in/py_runtime.h"

#include <cmath>

#include "runtime/cpp/gen/std/math.h"

namespace pytra::std::math {

float64 pi = static_cast<float64>(3.141592653589793);
float64 e = static_cast<float64>(2.718281828459045);

float64 sqrt(float64 x) {
    return static_cast<float64>(::std::sqrt(x));
}

float64 sin(float64 x) {
    return static_cast<float64>(::std::sin(x));
}

float64 cos(float64 x) {
    return static_cast<float64>(::std::cos(x));
}

float64 tan(float64 x) {
    return static_cast<float64>(::std::tan(x));
}

float64 exp(float64 x) {
    return static_cast<float64>(::std::exp(x));
}

float64 log(float64 x) {
    return static_cast<float64>(::std::log(x));
}

float64 log10(float64 x) {
    return static_cast<float64>(::std::log10(x));
}

float64 fabs(float64 x) {
    return static_cast<float64>(::std::fabs(x));
}

float64 floor(float64 x) {
    return static_cast<float64>(::std::floor(x));
}

float64 ceil(float64 x) {
    return static_cast<float64>(::std::ceil(x));
}

float64 pow(float64 x, float64 y) {
    return static_cast<float64>(::std::pow(x, y));
}

}  // namespace pytra::std::math
