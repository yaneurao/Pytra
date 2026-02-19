// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/math.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_CPP_MODULE_MATH_H
#define PYTRA_CPP_MODULE_MATH_H

#include <any>

namespace pytra::core::math {

double sqrt(double x);
double sin(double x);
double cos(double x);
double exp(double x);
double tan(double x);
double log(double x);
double log10(double x);
double fabs(double x);
double floor(double x);
double ceil(double x);
double pow(double x, double y);
double sqrt(const std::any& x);
double sin(const std::any& x);
double cos(const std::any& x);
double exp(const std::any& x);
double tan(const std::any& x);
double log(const std::any& x);
double log10(const std::any& x);
double fabs(const std::any& x);
double floor(const std::any& x);
double ceil(const std::any& x);
double pow(const std::any& x, const std::any& y);
extern const double pi;
extern const double e;

}  // namespace pytra::core::math

namespace pytra {
namespace math = core::math;
}

#endif  // PYTRA_CPP_MODULE_MATH_H
