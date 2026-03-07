# pytra-core

`src/runtime/cpp/core/` は C++ low-level runtime の stable include surface です。

## ルール

- 現在は stable include surface の forwarder header だけを置き、handwritten core の正本 header / compile source は `src/runtime/cpp/native/core/` に置く。
- `runtime/cpp/native/core/...` を直接 include してよいのは、この `core/` 配下の forwarder header だけとする。generated runtime / native companion / backend 出力は常に `runtime/cpp/core/...` を踏む。
- 将来 pure Python SoT から変換する core artifact は `src/runtime/cpp/generated/core/` に置き、`core/` に直接混在させない。
- `pytra/core/` は導入しない。low-level core の include root は `core/...` を維持する。
- `src/runtime/cpp/generated/{std,utils,built_in}/` と
  `src/runtime/cpp/native/{std,built_in}/` から include される前提で、
  依存方向は `generated/native -> core` を維持する。

## 目的

- 既存 include 契約を崩さずに、low-level core でも generated/handwritten の ownership 混在を防ぐ。
