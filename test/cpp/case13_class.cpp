#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case13_class.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Multiplier {
    int64 mul(int64 x, int64 y) {
        return x * y;
    }
};

int main() {
    Multiplier m = Multiplier();
    py_print(m.mul(6, 7));
    return 0;
}
