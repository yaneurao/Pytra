#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case17_loop.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 calc_17(list<int64> values) {
    int64 total = 0;
    for (int64 v : values) {
        if (v % 2 == 0)
            total = total + v;
        else
            total = total + v * 2;
    }
    return total;
}

int main() {
    py_print(calc_17(list<int64>{1, 2, 3, 4}));
    return 0;
}
