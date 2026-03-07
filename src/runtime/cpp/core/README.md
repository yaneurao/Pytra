# pytra-core

`src/runtime/cpp/core/` は C++ low-level runtime の stable include surface です。

## ルール

- 現在は stable include surface の header だけを置き、compile source は `src/runtime/cpp/native/core/` に置く。
- 将来 pure Python SoT から変換する core artifact は `src/runtime/cpp/generated/core/` に置き、`core/` に直接混在させない。
- `pytra/core/` は導入しない。low-level core の include root は `core/...` を維持する。
- `src/runtime/cpp/generated/{std,utils,built_in}/` と
  `src/runtime/cpp/native/{std,built_in}/` から include される前提で、
  依存方向は `generated/native -> core` を維持する。

## 目的

- 既存 include 契約を崩さずに、low-level core でも generated/handwritten の ownership 混在を防ぐ。
