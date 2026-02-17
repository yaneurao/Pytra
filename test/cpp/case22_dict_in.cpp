#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_dict_in.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

bool has_key_23(str k) {
    dict<str, int64> d = dict<str, int64>{{"a", 1}, {"b", 2}};
    if (d.find(k) != d.end())
        return true;
    else
        return false;
}

int main() {
    py_print(has_key_23("a"));
    return 0;
}
