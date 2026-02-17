// このファイルは `test/py/case02_sub_mul.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case02_sub_mul.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 calc(int64 x, int64 y) {
    return (x - y) * 2;
}

float64 div_calc(int64 x, int64 y) {
    return static_cast<float64>(x) / static_cast<float64>(y);
}

int main() {
    py_print(calc(9, 4));
    py_print(div_calc(9, 4));
    return 0;
}
