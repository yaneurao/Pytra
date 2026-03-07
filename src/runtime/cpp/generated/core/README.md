# pytra-generated-core

`src/runtime/cpp/generated/core/` は、pure Python SoT から変換された low-level core artifact の正本置き場です。

## ルール

- `generated/core/` に置くコードは `source:` と `generated-by:` marker を必須にする。
- include 面は増やさず、public/stable include は引き続き `src/runtime/cpp/core/*.ext.h` を使う。
- compile/source 解決は `core/...` public header から `generated/core/...` と `native/core/...` を導出する。
- real artifact がまだ無い段階でも、このディレクトリ自体は正式レイアウトとして維持する。

## 置いてよいもの

- pure Python SoT から機械変換でき、`core/...` の public include 名を壊さずに追加できる low-level helper。
- `native/core` を直接 include せず、`core/...` public header か self-contained generated header だけで完結する artifact。
- C++ 固有の ownership / ABI glue / OS 接着を持たず、`generated-by` marker 付き checked-in artifact として再生成可能なもの。

## まだ置いてはいけないもの

- `gc`, `io`, object/container 表現、RC/GC、例外/I/O 集約など、C++ 固有の layout や lifetime 管理に依存する helper。
- `std` / `built_in` / `utils` module runtime を `core` へ逆流入させる高レベル実装。
- template / inline の都合で `native/core` 正本に寄せるべき handwritten helper。
