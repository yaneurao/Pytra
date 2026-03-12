# pytra-native

`src/runtime/cpp/native/` は C++ 固有 companion を置く layer です。

## ルール

- 宣言の正本は原則 `src/runtime/cpp/generated/` に置く。
- `native/` には SoT から生成できない C++ 固有処理だけを置く。
- `native/*.h` は template / inline helper など本当に必要なものだけに限定する。
- `native/core/` には low-level runtime の handwritten 正本 header / source を置き、compiler include 面もここを正本とする。
- `src/runtime/cpp/core/` は export/sdk compatibility surface であり、compiler include 正本ではない。
- legacy module dir (`src/runtime/cpp/std/`, `src/runtime/cpp/built_in/`, `src/runtime/cpp/utils/`) には実装本体を置かない。
- `src/runtime/cpp/pytra/` shim は public/export include 面として残ってよいが、compiler include 正本には使わない。

## 配置境界

- `src/runtime/cpp/core/`: low-level runtime の export/sdk compatibility surface
- `src/runtime/cpp/generated/core/`: low-level core の generated lane
- `src/runtime/cpp/native/core/`: low-level core の handwritten 正本
- `src/runtime/cpp/generated/std/`: `pytra.std.*` の generated runtime
- `src/runtime/cpp/native/std/`: `pytra.std.*` の native companion
- `src/runtime/cpp/generated/built_in/`: `pytra.built_in.*` の generated runtime
- `src/runtime/cpp/native/built_in/`: `pytra.built_in.*` の native helper header
- `src/runtime/cpp/generated/utils/`: `pytra.utils.*` の generated runtime
