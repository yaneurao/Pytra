# pytra-generated-core

`src/runtime/cpp/generated/core/` は、pure Python SoT から変換された low-level core artifact の正本置き場です。

## ルール

- `generated/core/` に置くコードは `source:` と `generated-by:` marker を必須にする。
- include 面は増やさず、public/stable include は引き続き `src/runtime/cpp/core/*.ext.h` を使う。
- compile/source 解決は `core/...` public header から `generated/core/...` と `native/core/...` を導出する。
- real artifact がまだ無い段階でも、このディレクトリ自体は正式レイアウトとして維持する。
