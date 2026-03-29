<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-dict-items-sugar-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-dict-items-sugar-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-dict-items-sugar-retirement.md`

# P0: C++ `py_runtime.h` `py_dict_items` sugar 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTITEMS-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [src/runtime/cpp/native/core/py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h)

背景:
- `py_dict_items(const dict<K, V>&)` は tuple boxing を含む convenience helper であり、runtime に残る高水準 sugar の一つである。
- checked-in callsite が限定的なら、callsite 側 explicit loop へ寄せて `py_runtime.h` から外せる。

目的:
- `py_dict_items` の checked-in 依存を棚卸しし、不要なら helper を削除する。

対象:
- `py_dict_items(const dict<K, V>&)`

非対象:
- `py_dict_keys` / `py_dict_values`

受け入れ基準:
- checked-in callsite が明確になっている。
- representative callsite を explicit tuple boxing loop へ置換するか、未使用を確定している。
- helper 削除後の inventory guard がある。

確認コマンド:
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py`
- `python3 tools/check/check_todo_priority.py`

## タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01] `py_dict_items` sugar を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S1-02] explicit loop 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S2-02] helper を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: `py_runtime.h` の高水準 dict sugar をさらに減らす tranche として `py_dict_items` を分離した。
- 2026-03-09: checked-in source を棚卸しすると、`py_dict_items(const dict<K, V>&)` の direct callsite は helper 自身と runtime inventory guard だけで、runtime / emitter / generated code に残存利用は無かった。
- 2026-03-09: representative callsite の explicit loop 置換対象は存在しないと判断し、`S2-01` は no-op 完了として扱う。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から `py_dict_items(const dict<K, V>&)` を削除し、`test_cpp_runtime_iterable.py` に inventory guard を追加した。
- 2026-03-09: verification は `test_cpp_runtime_iterable.py`、`test_py2cpp_codegen_issues.py`、`check_todo_priority.py` を通した。
