# P0: C++ `py_runtime.h` `object`-`nullopt` 比較 compat 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [src/runtime/cpp/native/core/py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h)

背景:
- `py_runtime.h` には `object == std::nullopt` / `!=` の compat operator が 4 本残っている。
- これは旧 selfhost / optional compat の名残で、明示的な `!obj` / `obj.has_value()` へ寄せられる可能性が高い。

目的:
- `object`-`nullopt` 比較 compat の checked-in 依存を棚卸しし、不要なら削除する。

対象:
- `operator==(const object&, const ::std::nullopt_t&)`
- `operator!=(const object&, const ::std::nullopt_t&)`
- `operator==(const ::std::nullopt_t&, const object&)`
- `operator!=(const ::std::nullopt_t&, const object&)`

非対象:
- `optional<T>` 自体の比較

受け入れ基準:
- checked-in callsite が明確になっている。
- representative callsite が explicit null check へ置換されるか、未使用が確定している。
- helper 削除後の inventory guard がある。

確認コマンド:
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_east3_cpp_bridge.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `python3 tools/check_todo_priority.py`

## タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01] `object`-`nullopt` 比較 compat を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01-S1-02] explicit null check 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01-S2-02] operator 群を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-NULLOPT-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: `object` public convenience の整理を継続する tranche として、`nullopt` 比較 compat を個別に扱う。
- 2026-03-09: checked-in source を棚卸しすると、`object == ::std::nullopt` / `!=` の direct callsite は helper 自身以外に見つからなかった。`test_py2cpp_codegen_issues.py` の `::std::nullopt` assertion は optional 初期化の回帰であり、本 operator 群には依存していない。
- 2026-03-09: explicit null check への representative 置換対象は存在しないと判断し、`S2-01` は no-op 完了として扱う。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から `object`-`nullopt` 比較 compat 4 本を削除し、`test_cpp_runtime_iterable.py` に inventory guard を追加した。
- 2026-03-09: verification は `test_east3_cpp_bridge.py`、`test_cpp_runtime_iterable.py`、`check_todo_priority.py` を通した。
