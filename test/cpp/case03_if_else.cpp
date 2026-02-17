// このファイルは `test/py/case03_if_else.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case03_if_else.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 abs_like(int64 n) {
    if (n < 0)
        return -n;
    else
        return n;
}

int main() {
    py_print(abs_like(-12));
    return 0;
}
