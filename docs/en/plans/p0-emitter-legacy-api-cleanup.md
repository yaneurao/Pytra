<a href="../../ja/plans/p0-emitter-legacy-api-cleanup.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-emitter-legacy-api-cleanup.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-emitter-legacy-api-cleanup.md`

# P0: emitter 旧 API 出力の一掃 — runtime API 移行残り

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EMITTER-LEGACY-API-CLEANUP-02`

## 背景

P0-4 で runtime の旧 object API（`make_object`, `obj_to_rc_or_raise` 等）を新 API（`object(...)`, `object::as<T>()` 等）に移行した。しかし C++ emitter が生成するコードの一部にまだ旧 API 呼び出しが残っており、`test_py2cpp_features.py` のコンパイルテスト（~100件）が g++ エラーで失敗している。

### 確認済みの旧 API パターン

| 旧 API（emitter が生成）| 新 API（runtime が提供）| 影響 |
|---|---|---|
| `object_new(...)` | `object(...)` コンストラクタ | Any 型の生成 |
| `PyListObj` | `list<object>` | Any list 型 |
| `obj_to_list_ref_or_raise(x)` | `x.as<list<T>>()` | list unbox |
| `py_object_try_cast<T>(x)` | `x.as<T>()` | object cast |
| `py_list_at_ref(obj, i)` | `obj.as<list<T>>()[i]` | list index |
| `py_at(tuple, i)` | `std::get<i>(tuple)` | tuple index |
| `pytra::utils::*` | include パス不足 | namespace 解決 |
| `dict<str, int>` → `object` 変換 | `object(dict)` コンストラクタ | dict box |

### 影響範囲

- `test_py2cpp_features.py`: ~100件の transpile → compile → run テスト
- `test_cpp_runtime_type_id.py`: 2件の type_id API テスト
- emitter ソース: `src/toolchain/emit/cpp/emitter/` 配下の複数ファイル

## 対象

- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` — `object_new`, `PyListObj` 等の旧 API 生成箇所
- `src/toolchain/emit/cpp/emitter/call.py` — `obj_to_list_ref_or_raise`, `py_object_try_cast` 等
- `src/toolchain/emit/cpp/emitter/expr.py` — `py_list_at_ref`, `py_at` 等
- `src/toolchain/emit/cpp/emitter/collection_expr.py` — dict/list リテラルの object 変換
- `test/unit/backends/cpp/test_cpp_runtime_type_id.py` — テストアサーションの API 名更新

## 非対象

- runtime 側の変更（runtime は新 API に移行済み）
- 非 C++ backend の修正
- P0-12（CLI オプション転送）— テストの呼び出し経路の問題は本タスクのスコープ外

## 受け入れ基準

- [ ] `test_py2cpp_features.py` の全コンパイルテストが g++ で通る。
- [ ] `test_cpp_runtime_type_id.py` の全テストが通る。
- [ ] emitter が旧 API 名（`object_new`, `PyListObj`, `obj_to_list_ref_or_raise`, `py_object_try_cast`）を生成しない。

## 子タスク

- [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S1] emitter の `object_new` / `PyListObj` 生成箇所を `object(...)` / `list<object>` に置換。
- [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S2] emitter の `obj_to_list_ref_or_raise` / `py_object_try_cast` を `object::as<T>()` に置換。
- [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S3] emitter の `py_list_at_ref` / `py_at(tuple)` — runtime に現存する正当な API。置換不要。
- [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S4] `pytra::utils` namespace の include パス — 既に正しく動作。修正不要。
- [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S5] テストアサーション（`test_cpp_runtime_type_id.py`）を新 API に追従。

## 決定ログ

- 2026-03-21: P0-14（string_ops.h 欠落）解消後、test_py2cpp_features.py の compile 失敗が旧 API 名に起因することを特定。P0-4 で対応済みと見做していたが、emitter の一部コードパスに旧 API 生成が残存していた。
- 2026-03-21: S3/S4 調査。`py_list_at_ref` / `py_at` は runtime ヘッダー（list_ops.h, dict_ops.h）に現存する正当な API であり、generated コード（json.cpp, pathlib.cpp）からも使用されている。置換不要と判断。`pytra::utils` namespace の include パスも `#include "utils/gif.h"` + `pytra::utils::gif::*` として正しく動作しており修正不要。S1〜S5 全完了。
