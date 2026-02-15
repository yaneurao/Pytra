// このファイルは Python の `math` モジュール互換実装の本体です。

#include <cmath>

#include "cpp_module/math.h"

namespace pycs::cpp_module::math {

double sqrt(double x) {
    return std::sqrt(x);
}

}  // namespace pycs::cpp_module::math
