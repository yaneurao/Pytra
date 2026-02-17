#include "cpp_module/py_runtime.h"

void __pytra_main() {
    list<int64> l = list<int64>{1, 2, 3};
    int64 sum = 0;
    for (int64 v : l)
        sum += v;
    py_print(sum);
}

int main() {
    __pytra_main();
    return 0;
}
