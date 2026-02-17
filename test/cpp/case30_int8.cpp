#include "cpp_module/py_runtime.h"

void __pytra_main() {
    int8 i = 1;
    py_print(i * 2);
}

int main() {
    __pytra_main();
    return 0;
}
