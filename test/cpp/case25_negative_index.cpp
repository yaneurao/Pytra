#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case25_negative_index.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 last_item_25() {
    list<int64> stack = list<int64>{10, 20, 30, 40};
    return py_at(stack, -1);
}

int main() {
    py_print(last_item_25());
    return 0;
}
