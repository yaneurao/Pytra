# pytra-std

`src/runtime/cpp/std/` は `pytra.std.*` の補足文書レイヤです。native companion 本体は `src/runtime/cpp/native/std/` へ移行しました。

## ルール

- `generated/std/` に置けない C++ 固有 companion は `src/runtime/cpp/native/std/` に置く。
- `src/runtime/cpp/std/` 直下には実装本体を置かない。
- 自動生成物は `src/runtime/cpp/generated/std/` に置く。
- public include は `src/runtime/cpp/pytra/std/` から参照する。

## 配置境界

- `src/runtime/cpp/core/`: 手書きの低レベル runtime
- `src/runtime/cpp/generated/std/`: `pytra.std.*` の generated runtime
- `src/runtime/cpp/native/std/`: `pytra.std.*` の native companion
- `src/runtime/cpp/generated/utils/`: `pytra.utils.*` の generated runtime
- `src/runtime/cpp/generated/built_in/`: `pytra.built_in.*` の generated runtime
- `src/runtime/cpp/native/built_in/`: `pytra.built_in.*` の native helper header
