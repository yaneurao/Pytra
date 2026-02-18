// このファイルは Python の `math` モジュール互換の最小実装です。
// 現時点ではトランスパイラが利用する `sqrt` を提供します。

#ifndef PYTRA_CPP_MODULE_MATH_H
#define PYTRA_CPP_MODULE_MATH_H

namespace pytra::cpp_module::math {

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
extern const double pi;
extern const double e;

}  // namespace pytra::cpp_module::math

#endif  // PYTRA_CPP_MODULE_MATH_H
