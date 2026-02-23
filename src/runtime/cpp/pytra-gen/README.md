# pytra-gen

`src/runtime/cpp/pytra-gen/` は C++ runtime の自動生成レイヤ専用です。

## ルール

- `AUTO-GENERATED FILE. DO NOT EDIT.` ヘッダを持つファイルのみ配置する。
- 手書き実装（`-impl.*` や `built_in` のコア実装）は置かない。
- 生成元は `src/pytra/` と `src/py2cpp.py --emit-runtime-cpp` を正本とする。

## 目的

- `src/runtime/cpp/pytra-core/`（手書き）との責務分離を明示し、移行時の配置先を固定する。
