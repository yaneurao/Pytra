#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case33_dataclass.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Point99 {
    int64 x;
    int64 y;
    
    Point99(int64 x, int64 y = 10) {
        this->x = x;
        this->y = y;
    }
    
    int64 total() {
        return this->x + this->y;
    }
};

int main() {
    Point99 p = Point99(3);
    py_print(p.total());
    return 0;
}
