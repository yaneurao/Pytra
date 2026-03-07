# pytra-std

`src/runtime/cpp/std/` は `pytra.std.*` の native companion を置く C++ runtime の標準ライブラリ層です。

## ルール

- `generated/std/` に置けない C++ 固有 companion だけを置く。
- 現行移行期間では手書き TU は `*.ext.cpp` のまま残す。
- 自動生成物は `src/runtime/cpp/generated/std/` に置く。
- public include は `src/runtime/cpp/pytra/std/` から参照する。

## 配置境界

- `src/runtime/cpp/core/`: 手書きの低レベル runtime
- `src/runtime/cpp/generated/std/`: `pytra.std.*` の generated runtime
- `src/runtime/cpp/std/`: `pytra.std.*` の native companion（現行は `*.ext.cpp`）
- `src/runtime/cpp/utils/`: `pytra.utils.*` の生成物
- `src/runtime/cpp/built_in/`: `pytra.built_in.*` の生成物
