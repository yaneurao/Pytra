#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case08_nested_call.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 inc(int64 x) {
    return x + 1;
}

int64 twice(int64 x) {
    return inc(inc(x));
}

int main() {
    py_print(twice(10));
    return 0;
}
