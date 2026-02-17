#include "cpp_module/py_runtime.h"

// 同一インスタンス共有のテスト。
// 参照セマンティクスが壊れると a,b の値が一致しない。


struct Box : public PyObj {
    int64 v;
    
    Box(int64 v) {
        this->v = v;
    }
};

void bump(const rc<Box>& x) {
    x->v++;
}

void run_case35_alias_arg() {
    rc<Box> a = rc_new<Box>(1);
    rc<Box> b = a;
    bump(b);
    py_print(a->v);
    py_print(b->v);
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_case35_alias_arg();
    return 0;
}
