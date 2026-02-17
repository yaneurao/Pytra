#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case34_gc_reassign.py` のテスト/実装コードです。
// a = b の再代入で参照が切れたオブジェクトが破棄されることを確認します。


struct Tracked : public PyObj {
    str name;
    
    Tracked(const str& name) {
        this->name = name;
    }
    ~Tracked() {
        py_print("DEL", this->name);
    }
};

void run_case34_gc_reassign() {
    rc<Tracked> a = ::rc_new<Tracked>("A");
    rc<Tracked> b = ::rc_new<Tracked>("B");
    py_print("before reassign");
    a = b;
    py_print("after reassign");
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_case34_gc_reassign();
    return 0;
}
