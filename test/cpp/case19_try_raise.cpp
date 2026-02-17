#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case19_try_raise.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 maybe_fail_19(bool flag) {
    try {
        if (flag) {
            throw std::runtime_error("fail-19");
        }
        return 10;
    }
    catch (const std::exception& ex) {
        return 20;
    }
    {
    }
}

int main() {
    py_print(maybe_fail_19(true));
    return 0;
}
