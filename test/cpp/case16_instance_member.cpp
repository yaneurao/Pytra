// このファイルは `test/py/case16_instance_member.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case16_instance_member.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Point {
    int64 x;
    int64 y;
    
    Point(int64 x, int64 y) {
        this->x = x;
        this->y = y;
    }
    int64 total() {
        return this->x + this->y;
    }
};

int main() {
    Point p = Point(2, 5);
    py_print(p.total());
    return 0;
}
