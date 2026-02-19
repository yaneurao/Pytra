// このファイルは Python の `math` モジュール互換の最小実装です。
// 現時点ではトランスパイラが利用する `sqrt` を提供します。

#ifndef PYTRA_CPP_MODULE_MATH_H
#define PYTRA_CPP_MODULE_MATH_H

#include <any>

namespace pytra::core::math {

/**
 * @brief 平方根を返します（Python の `math.sqrt` 相当）。
 * @param x 非負の実数値。
 * @return x の平方根。
 */
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
