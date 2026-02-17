// このファイルは `test/py/case33_ifexp_bool.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_ifexp_bool.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 pick_25(int64 a, int64 b, bool flag) {
    int64 c = ((flag) && (a > b) ? a : b);
    return c;
}

int main() {
    py_print(pick_25(10, 3, true));
    return 0;
}
