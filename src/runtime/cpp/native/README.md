# pytra-native

`src/runtime/cpp/native/` は C++ 固有 companion を置く layer です。

## ルール

- 宣言の正本は原則 `src/runtime/cpp/generated/` に置く。
- `native/` には SoT から生成できない C++ 固有処理だけを置く。
- `native/*.h` は template / inline helper など本当に必要なものだけに限定する。
- `native/core/` には low-level runtime の handwritten 正本 header / source を置き、public include 面は `src/runtime/cpp/core/` forwarder から維持する。
- `native/core/...` は ownership 正本であって include 正本ではない。`core/` forwarder 以外から直接 include しない。
- legacy module dir (`src/runtime/cpp/std/`, `src/runtime/cpp/built_in/`, `src/runtime/cpp/utils/`) には実装本体を置かない。
- public include は `src/runtime/cpp/pytra/` shim を経由する。

## 配置境界

- `src/runtime/cpp/core/`: low-level runtime の stable include surface
- `src/runtime/cpp/generated/core/`: low-level core の generated lane
- `src/runtime/cpp/native/core/`: low-level core の handwritten 正本
- `src/runtime/cpp/generated/std/`: `pytra.std.*` の generated runtime
- `src/runtime/cpp/native/std/`: `pytra.std.*` の native companion
- `src/runtime/cpp/generated/built_in/`: `pytra.built_in.*` の generated runtime
- `src/runtime/cpp/native/built_in/`: `pytra.built_in.*` の native helper header
- `src/runtime/cpp/generated/utils/`: `pytra.utils.*` の generated runtime
