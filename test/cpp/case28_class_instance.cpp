// このファイルは `test/py/case33_class_instance.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_class_instance.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Box100 {
    int64 seed;
    
    Box100(int64 seed) {
        this->seed = seed;
    }
    int64 next() {
        this->seed++;
        return this->seed;
    }
};

int main() {
    Box100 b = Box100(3);
    py_print(b.next());
    return 0;
}
