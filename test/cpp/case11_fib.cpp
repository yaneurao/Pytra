// このファイルは `test/py/case11_fib.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。


#include "cpp_module/py_runtime.h"

// このファイルは `test/py/case11_fib.py` のテスト/実装コードです。
// 役割が分かりやすいように、読み手向けの説明コメントを付与しています。
// 変更時は、既存仕様との整合性とテスト結果を必ず確認してください。

int64 fib(int64 n) {
    if (n <= 1)
        return n;
    
    return fib(n - 1) + fib(n - 2);
}

int main() {
    py_print(fib(10));
    return 0;
}
