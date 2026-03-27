<a href="../../ja/plans/p0-py-runtime-h-decomposition.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-py-runtime-h-decomposition.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-py-runtime-h-decomposition.md`

# P0: py_runtime.h 分解・廃止

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PY-RUNTIME-H-DECOMPOSITION-01`
- 前提: P0-SELF-CONTAINED-CPP-OUTPUT-01-S7（循環依存解消）を包含

## 背景

`py_runtime.h` は 268 行のモノリシックヘッダーで、C++ runtime の全機能を 1 ファイルに集約している。エミッターは `#include "core/py_runtime.h"` を固定で emit しており、必要のないヘッダーも全て読み込まれる。

### 問題

1. **循環依存**: `py_runtime.h` → `type_id.h` → `py_runtime_value_isinstance`（`py_runtime.h` 後半）の循環。`out/cpp/` 自己完結ビルドのブロッカー。
2. **不要な依存**: 単純な数値計算プログラムでも `type_id.h` や `variant` が読み込まれる。
3. **エミッターの include が固定**: `resolved_dependencies_v1` で依存を確定しても、`py_runtime.h` が全てを束ねるので粒度が活かせない。

## 設計

### 分割先

`py_runtime.h` の中身を以下の 6 ファイルに分割する。各ファイルは独立して include 可能。

| 分割先 | 行 | 内容 | 依存 |
|--------|-----|------|------|
| `core/str_methods.h` | 31-49 | `str::split`, `str::join` 等のインライン委譲 | `core/py_types.h`, `built_in/string_ops.h` |
| `core/conversions.h` | 53-95 | `py_to`, `py_to_bool`, `py_variant_to_bool`, `py_is_list_type` | `core/py_types.h` |
| `built_in/dict_ops.h` | 104-147 | `py_at(dict)`, `py_index` | `core/py_types.h` |
| `built_in/bounds.h` | 149-179 | `py_at_bounds`, `py_at_bounds_debug` | `core/py_types.h` |
| `core/type_id_support.h` | 191-258 | `py_runtime_type_id_is_subtype`, `py_runtime_value_isinstance`, `py_runtime_value_type_id` 等 | `core/py_types.h`, `built_in/type_id.h` |
| `core/rc_ops.h` | 261-264 | `operator-(rc<T>)` | `core/py_types.h` |

### 標準ライブラリ include (1-17)

分割後の各ヘッダーが必要な `<algorithm>`, `<variant>` 等を自分で include する。`py_runtime.h` が束ねる必要はない。

### エミッターの変更

エミッターは `resolved_dependencies_v1` に基づいて必要なヘッダーだけを個別に emit する。

例: 数値計算のみのプログラム
```cpp
#include "core/py_types.h"
#include "core/conversions.h"
#include "built_in/io_ops.h"
```

例: isinstance を使うプログラム
```cpp
#include "core/py_types.h"
#include "core/conversions.h"
#include "core/type_id_support.h"
#include "built_in/type_id.h"
#include "built_in/io_ops.h"
```

### py_runtime.h の残存

分割完了後、`py_runtime.h` は全ヘッダーを include するだけの互換ファサードとして残す。selfhost や既存テストが参照しているため、即時削除はしない。新規 emit では使わない。

```cpp
// py_runtime.h — compatibility facade (deprecated)
#include "core/py_types.h"
#include "core/exceptions.h"
#include "core/io.h"
#include "built_in/base_ops.h"
#include "built_in/string_ops.h"
#include "core/str_methods.h"
#include "core/conversions.h"
#include "built_in/list_ops.h"
#include "built_in/dict_ops.h"
#include "built_in/bounds.h"
#include "built_in/type_id.h"
#include "core/type_id_support.h"
#include "core/rc_ops.h"
```

### 循環依存の解消

分割により循環が解消される:
- `type_id.h` は `core/type_id_support.h` に依存しない（逆向き）
- `core/type_id_support.h` は `built_in/type_id.h` に依存する
- `py_runtime.h` のファサードで `type_id.h` → `type_id_support.h` の順に include すれば循環なし

## 対象ファイル

| ファイル | 変更 |
|---------|------|
| `src/runtime/cpp/core/py_runtime.h` | 中身を 6 ファイルに分割、ファサード化 |
| `src/runtime/cpp/core/str_methods.h` | 新規作成 |
| `src/runtime/cpp/core/conversions.h` | 新規作成 |
| `src/runtime/cpp/built_in/dict_ops.h` | 新規作成 |
| `src/runtime/cpp/built_in/bounds.h` | 新規作成 |
| `src/runtime/cpp/core/type_id_support.h` | 新規作成 |
| `src/runtime/cpp/core/rc_ops.h` | 新規作成 |
| `src/toolchain/emit/cpp/emitter/module.py` | `py_runtime.h` 固定 emit → 個別ヘッダー emit |
| `src/toolchain/emit/cpp/emitter/cpp_emitter.py` | `py_runtime.h` 参照除去 |
| `src/toolchain/emit/cpp/cli.py` | `py_runtime.h` 参照除去 |

## 非対象

- selfhost ビルドの `py_runtime.h` 参照（互換ファサードで維持）
- 非 C++ バックエンド

## 受け入れ基準

- [ ] `py_runtime.h` の実体が include のみのファサード（定義なし）。
- [ ] 分割後の各ヘッダーが独立して include 可能。
- [ ] エミッターが `py_runtime.h` ではなく個別ヘッダーを emit。
- [ ] `py_runtime.h` ↔ `type_id.h` の循環依存が解消。
- [ ] `out/cpp/` で g++ ビルドが通る。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S1] `core/str_methods.h` を分離する（`str::split` 等の委譲）。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S2] `core/conversions.h` を分離する（`py_to`, `py_to_bool`, `py_variant_to_bool`）。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S3] `built_in/dict_ops.h` を分離する（`py_at(dict)`, `py_index`）。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S4] `built_in/bounds.h` を分離する（`py_at_bounds`, `py_at_bounds_debug`）。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S5] `core/type_id_support.h` を分離する（`py_runtime_value_isinstance` 等）。循環依存解消。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S6] `core/rc_ops.h` を分離する（`operator-(rc<T>)`）。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S7] `py_runtime.h` を include のみのファサードに書き換える。
- [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S8] エミッターが `py_runtime.h` ではなく個別ヘッダーを emit するよう変更する。

## 決定ログ

- 2026-03-19: `py_runtime.h` ↔ `type_id.h` 循環依存が `out/cpp/` 自己完結ビルドのブロッカー。ユーザーから「py_runtime.h 自体をなくす方向で考えている」と方針提示。268 行を 6 ファイルに分割し、エミッターが個別 include を emit する設計で起案。
