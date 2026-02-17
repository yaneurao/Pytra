#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case04_assign.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 square_plus_one(int64 n) {
    int64 result = n * n;
    result++;
    return result;
}

int main() {
    py_print(square_plus_one(5));
    return 0;
}
