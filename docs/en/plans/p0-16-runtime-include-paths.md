<a href="../../ja/plans/p0-16-runtime-include-paths.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-16-runtime-include-paths.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-16-runtime-include-paths.md`

# P0-16: runtime include パスのテストアサーション不一致

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RUNTIME-INCLUDE-PATHS-01`

## 背景

`module_name_to_cpp_include` が `generated/` プレフィックスを除去するようになり、
また `py_runtime.h` のインクルードパスが変化したため、
`test_cpp_runtime_symbol_index_integration.py` の 6 件が失敗する。

### 変化1: `module_name_to_cpp_include` の戻り値
```python
# 旧
module_name_to_cpp_include("math")        == "generated/std/math.h"
module_name_to_cpp_include("pytra.std.time") == "generated/std/time.h"
module_name_to_cpp_include("pytra.core.dict") == "native/core/dict.h"
# 新
module_name_to_cpp_include("math")           == ""        # 変化あり
module_name_to_cpp_include("pytra.std.time")  == "std/time.h"
module_name_to_cpp_include("pytra.core.dict") == "core/dict.h"
```

### 変化2: 生成 C++ コード内の `#include` パス
```cpp
// 旧
#include "generated/std/time.h"
#include "runtime/cpp/core/py_runtime.h"
#include "generated/utils/png.h"
#include "runtime/east/compiler/transpile_cli.h"
// 新
#include "std/time.h"
#include "core/py_runtime.h"
#include "utils/png.h"
// ...
```

## 対象

- `tools/unittest/emit/cpp/test_cpp_runtime_symbol_index_integration.py` — 6 件

## 受け入れ基準

- [ ] 6 件のテストがパスする

## 子タスク

- [ ] [ID: P0-RUNTIME-INCLUDE-PATHS-01] テストアサーションを新しいインクルードパスに合わせて更新

## 決定ログ

- 2026-03-21: `runtime_paths.py` が `generated/` プレフィックスを strip するようになったことが判明。
  "math" が空文字列を返す点は別途調査が必要（モジュール名 "math" が索引に存在しない可能性）。
  テストアサーションを新実装に合わせて更新する。
