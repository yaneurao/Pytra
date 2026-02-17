// このファイルは `test/py/case12_string_ops.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case12_string_ops.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

str decorate(const str& name) {
    str prefix = "[USER] ";
    str message = prefix + name;
    return message + "!";
}

int main() {
    py_print(decorate("Alice"));
    return 0;
}
