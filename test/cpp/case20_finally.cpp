#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case20_finally.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 finally_effect_20(bool flag) {
    int64 value = 0;
    {
        auto __finally_1 = py_make_scope_exit([&]() {
            value = value + 3;
        });
        try {
            if (flag)
                throw std::runtime_error("fail-20");
            value = 10;
        }
        catch (const std::exception& ex) {
            value = 20;
        }
    }
    return value;
}

int main() {
    py_print(finally_effect_20(true));
    return 0;
}
