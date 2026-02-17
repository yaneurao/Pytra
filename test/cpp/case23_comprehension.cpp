#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_comprehension.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 comp_like_24(int64 x) {
    list<int64> values = [&]() -> list<int64> {     list<int64> __out;     for (auto i : list<int64>{1, 2, 3, 4}) {         __out.push_back(i);     }     return __out; }();
    return x + 1;
}

int main() {
    py_print(comp_like_24(5));
    return 0;
}
