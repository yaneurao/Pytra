#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_class_static.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Counter26 {
    inline static int64 total = 0;
    
    int64 add(int64 x) {
        Counter26::total = Counter26::total + x;
        return Counter26::total;
    }
};

int main() {
    Counter26 c = Counter26();
    py_print(c.add(5));
    return 0;
}
