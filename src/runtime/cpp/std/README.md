# pytra-std

`src/runtime/cpp/std/` は `src/pytra/std/*.py` を正本として生成される C++ runtime の標準ライブラリ層です。

## ルール

- `.h` は自動生成物を置く。
- `.cpp` も原則として自動生成物を置く。
- 手書き実装が必要な TU は `*.ext.cpp` という名前で同居させる。
- `AUTO-GENERATED FILE. DO NOT EDIT.` が付いたファイルは直接編集しない。

## 配置境界

- `src/runtime/cpp/core/`: 手書きの低レベル runtime
- `src/runtime/cpp/std/`: `pytra.std.*` の生成物（`*.gen.h/.gen.cpp`）と最小限の `*.ext.cpp`
- `src/runtime/cpp/utils/`: `pytra.utils.*` の生成物
- `src/runtime/cpp/built_in/`: `pytra.built_in.*` の生成物
