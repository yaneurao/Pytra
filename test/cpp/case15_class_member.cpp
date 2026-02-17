// このファイルは `test/py/case15_class_member.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case15_class_member.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Counter {
    inline static int64 value = 0;
    
    int64 inc() {
        Counter::value++;
        return Counter::value;
    }
};

int main() {
    Counter c = Counter();
    c.inc();
    c = Counter();
    py_print(c.inc());
    return 0;
}
