// このファイルは `test/py/case18_tuple_assign.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case18_tuple_assign.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 swap_sum_18(int64 a, int64 b) {
    int64 x = a;
    int64 y = b;
    py_swap(x, y);
    return x + y;
}

int main() {
    py_print(swap_sum_18(10, 20));
    return 0;
}
