#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case14_inheritance.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

struct Animal {
    str sound() {
        return "generic";
    }
};

struct Dog : public Animal {
    str bark() {
        return this->sound() + "-bark";
    }
};

int main() {
    Dog d = Dog();
    py_print(d.bark());
    return 0;
}
