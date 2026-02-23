# pytra-core

`src/runtime/cpp/pytra-core/` は C++ runtime の手書きコア実装専用です。

## ルール

- `AUTO-GENERATED FILE. DO NOT EDIT.` ヘッダを持つファイルは置かない。
- GC/ABI/低レベル補助など、生成しにくい最小コアのみを配置する。
- `src/runtime/cpp/pytra-gen/` から include される前提で、依存方向は `pytra-gen -> pytra-core` を維持する。

## 目的

- 自動生成レイヤを厚く、手書きレイヤを薄く保つ方針を配置規約として固定する。
