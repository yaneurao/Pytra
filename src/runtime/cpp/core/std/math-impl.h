#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_MATH_IMPL_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_MATH_IMPL_H

namespace pytra::std::math_impl {

extern const double pi;
extern const double e;

double sqrt(double x);
double sin(double x);
double cos(double x);
double tan(double x);
double exp(double x);
double log(double x);
double log10(double x);
double fabs(double x);
double floor(double x);
double ceil(double x);
double pow(double x, double y);

}  // namespace pytra::std::math_impl

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_MATH_IMPL_H
