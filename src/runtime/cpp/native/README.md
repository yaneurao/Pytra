# pytra-native

`src/runtime/cpp/native/` は C++ 固有 companion を置く layer です。

## ルール

- 宣言の正本は原則 `src/runtime/cpp/generated/` に置く。
- `native/` には SoT から生成できない C++ 固有処理だけを置く。
- `native/*.h` は template / inline helper など本当に必要なものだけに限定する。
- public include は `src/runtime/cpp/pytra/` shim を経由する。
