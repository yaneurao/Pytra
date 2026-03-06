# pytra-gen

`src/runtime/cpp/gen/` は C++ runtime の自動生成レイヤ（`built_in` 以外）専用です。

## ルール

- `AUTO-GENERATED FILE. DO NOT EDIT.` ヘッダを持つファイルのみ配置する。
- 手書き実装（`-impl.*` など）は置かない。
- `built_in` の自動生成物は `src/runtime/cpp/built_in/` に置く。
- 生成元は `src/pytra/` と `src/py2cpp.py --emit-runtime-cpp` を正本とする。

## 目的

- `src/runtime/cpp/core/`（手書き）との責務分離を明示し、移行時の配置先を固定する。
