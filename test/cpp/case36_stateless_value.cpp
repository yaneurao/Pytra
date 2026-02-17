#include "cpp_module/py_runtime.h"

// 値型最適化候補のテスト（インスタンス状態なし）。


struct Tag {
    int64 id() {
        return 7;
    }
};

void run_case36_stateless_value() {
    Tag t = Tag();
    Tag u = t;
    py_print(t.id());
    py_print(u.id());
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    run_case36_stateless_value();
    return 0;
}
