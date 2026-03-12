# pytra-generated-core

`src/runtime/cpp/generated/core/` は、pure Python SoT から変換された low-level core artifact の正本置き場です。

## ルール

- `generated/core/` に置くコードは `source:` と `generated-by:` marker を必須にする。
- 生成は `src/py2x.py --emit-runtime-cpp` の正規導線のみを使い、core helper 専用 generator は追加しない。
- compiler/include 面は `src/runtime/cpp/native/core/*.h` と `src/runtime/cpp/generated/core/*.h` の ownership lane だけを使う。
- compile/source 解決は `native/core/...` と `generated/core/...` から直接導出する。
- `generated/core/` の real artifact は plain naming (`*.h`, `*.cpp`) のみを許可し、`.ext` / `.gen` suffix を再導入しない。
- real artifact がまだ無い段階でも、このディレクトリ自体は正式レイアウトとして維持する。
- `generated/core` は `native/core/py_runtime.h` の肥大化逃がし用 bucket ではない。`built_in` semantics をここへ流し込んではならない。

## 置いてよいもの

- pure Python SoT から機械変換でき、`native/core/...` compiler include 面を壊さずに追加できる low-level helper。
- `runtime/cpp/native/core/...` と self-contained generated header だけで完結する artifact。
- C++ 固有の ownership / ABI glue / OS 接着を持たず、`generated-by` marker 付き checked-in artifact として再生成可能なもの。

## まだ置いてはいけないもの

- `gc`, `io`, object/container 表現、RC/GC、例外/I/O 集約など、C++ 固有の layout や lifetime 管理に依存する helper。
- `std` / `built_in` / `utils` module runtime を `core` へ逆流入させる高レベル実装。
- template / inline の都合で `native/core` 正本に寄せるべき handwritten helper。
