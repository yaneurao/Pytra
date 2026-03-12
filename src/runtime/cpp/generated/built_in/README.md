# pytra-generated-built_in

`src/runtime/cpp/generated/built_in/` は、`src/pytra/built_in/*.py` を正本とする pure-Python built_in semantics の checked-in C++ artifact 置き場です。

## ルール

- 生成は `src/py2x.py --emit-runtime-cpp` の正規導線のみを使い、module 専用 generator を追加しない。
- real artifact は plain naming (`*.h`, `*.cpp`) と `source:` / `generated-by:` marker を必須とする。
- `.h` は `runtime/cpp/native/core/...` と sibling generated/native header だけを include し、shim/compat tree を compiler include 面として使ってはならない。
- `.cpp` は `runtime/cpp/native/core/py_runtime.h` と必要な `runtime/cpp/native/core/{process_runtime,scope_exit}.h`、および sibling generated header を include してよいが、C++ 専用 handwritten glue を埋め込んではならない。
- helper 境界で mutable container を value 受けしたい場合は `@abi` などの明示契約を使う。C++ backend 内部の ref-first 表現を helper ABI として固定してはならない。

## 置いてよいもの

- `str::split` / `splitlines` / `count` / `join` のような pure string helper。
- object-specialized `zip` / `sorted` / `sum` / `min` / `max` など、SoT に戻せる built_in semantics。
- `runtime/cpp/native/core/py_runtime.h` の low-level helper を利用するだけで閉じる checked-in artifact。

## 置いてはいけないもの

- `object` / `rc<>` / GC / process I/O / OS 接着の ownership をまたぐ low-level helper。
- `native/core` の肥大化を避けるためだけに押し込む core helper。
- `std` / `utils` runtime や target 固有 SDK glue。
