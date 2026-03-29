<a href="../../ja/plans/p0-14-gpp-compile-headers.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-14-gpp-compile-headers.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-14-gpp-compile-headers.md`

# P0-14: g++ コンパイルテストが built_in/string_ops.h を見つけられない

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-GPP-COMPILE-HEADERS-01`

## 背景

`py_runtime.h` は `#include "built_in/string_ops.h"` を参照するが、
P0-CPP-GENERATED-RUNTIME-PIPELINE-01 の作業でこのファイルが
`src/runtime/cpp/built_in/` から削除された（generated パスに移動）。

`test_cpp_runtime_iterable.py` / `test_cpp_runtime_type_id.py` / `test_py2cpp_features.py` の
`_runtime` テストは `-I src/runtime/cpp` フラグでコンパイルするため、
`src/runtime/cpp/built_in/string_ops.h` が見つからずコンパイルエラーになる。

```
fatal error: built_in/string_ops.h: No such file or directory
   11 | #include "built_in/string_ops.h"
```

## 対象

- `tools/unittest/emit/cpp/test_cpp_runtime_iterable.py` — コンパイル用 `-I` フラグ追加または stub ヘッダー生成
- `tools/unittest/emit/cpp/test_cpp_runtime_type_id.py` — 同上
- `tools/unittest/emit/cpp/test_py2cpp_features.py` の `_compile_and_run_fixture` 系

## 受け入れ基準

- [ ] `test_path_stringify_runtime_*` などコンパイル系テストがパスする
- [ ] `test_cpp_runtime_type_id.py` の 2 件がパスする

## 子タスク

- [ ] [ID: P0-GPP-COMPILE-HEADERS-01] `src/runtime/cpp/built_in/string_ops.h` を生成し g++ テストのコンパイルが通るようにする

## 決定ログ

- 2026-03-21: `string_ops.h` は `src/runtime/east/built_in/string_ops.east` から生成される。
  テストが使う `-I src/runtime/cpp` パスに `string_ops.h` が存在しないことが根本原因。
  `src/runtime/cpp/built_in/` に `generated/built_in/string_ops.h` への転送 include（proxy header）を置く、
  またはテストに `-I src/runtime/east` を追加する方針で対応する。
