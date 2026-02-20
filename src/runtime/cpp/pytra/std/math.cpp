// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/math.py
// generated-by: src/py2cpp.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include <cmath>

#include "runtime/cpp/pytra/std/math.h"

namespace pytra::std::math {

static double any_to_double(const ::std::any& v) {
    if (const auto* p = ::std::any_cast<double>(&v)) return *p;
    if (const auto* p = ::std::any_cast<float>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<long long>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<unsigned long long>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<long>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<unsigned long>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<int>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<unsigned>(&v)) return static_cast<double>(*p);
    if (const auto* p = ::std::any_cast<bool>(&v)) return *p ? 1.0 : 0.0;
    return 0.0;
}

const double pi = 3.141592653589793;
const double e = 2.718281828459045;

double sqrt(double x) { return ::std::sqrt(x); }
double sin(double x) { return ::std::sin(x); }
double cos(double x) { return ::std::cos(x); }
double tan(double x) { return ::std::tan(x); }
double exp(double x) { return ::std::exp(x); }
double log(double x) { return ::std::log(x); }
double log10(double x) { return ::std::log10(x); }
double fabs(double x) { return ::std::fabs(x); }
double floor(double x) { return ::std::floor(x); }
double ceil(double x) { return ::std::ceil(x); }
double pow(double x, double y) { return ::std::pow(x, y); }

double sqrt(const ::std::any& x) { return sqrt(any_to_double(x)); }
double sin(const ::std::any& x) { return sin(any_to_double(x)); }
double cos(const ::std::any& x) { return cos(any_to_double(x)); }
double tan(const ::std::any& x) { return tan(any_to_double(x)); }
double exp(const ::std::any& x) { return exp(any_to_double(x)); }
double log(const ::std::any& x) { return log(any_to_double(x)); }
double log10(const ::std::any& x) { return log10(any_to_double(x)); }
double fabs(const ::std::any& x) { return fabs(any_to_double(x)); }
double floor(const ::std::any& x) { return floor(any_to_double(x)); }
double ceil(const ::std::any& x) { return ceil(any_to_double(x)); }
double pow(const ::std::any& x, const ::std::any& y) { return pow(any_to_double(x), any_to_double(y)); }

}  // namespace pytra::std::math
