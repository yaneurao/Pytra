// case30: スライス構文 a[b:c] の基本テスト（stepなし）。


#include "cpp_module/py_runtime.h"

// case30: スライス構文 a[b:c] の基本テスト（stepなし）。

void __pytra_main() {
    list<int64> nums = list<int64>{10, 20, 30, 40, 50};
    str text = "abcdef";
    
    list<int64> mid_nums = py_slice(nums, 1, 4);
    str mid_text = py_slice(text, 2, 5);
    
    py_print(mid_nums[0]);
    py_print(mid_nums[2]);
    py_print(mid_text);
}

int main() {
    __pytra_main();
    return 0;
}
