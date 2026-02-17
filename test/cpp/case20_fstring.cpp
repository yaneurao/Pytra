#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case20_fstring.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

str make_msg_22(str name, int64 count) {
    return (py_to_string(name) + ":22:" + py_to_string(count));
}

int main() {
    py_print(make_msg_22("user", 7));
    return 0;
}
