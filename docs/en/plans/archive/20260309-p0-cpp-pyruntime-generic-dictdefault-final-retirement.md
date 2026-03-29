<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-generic-dictdefault-final-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-generic-dictdefault-final-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-generic-dictdefault-final-retirement.md`

# P0: C++ `py_runtime.h` 汎用 `py_dict_get_default` 最終退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [src/runtime/cpp/native/core/py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h)

背景:
- `py_runtime.h` にはまだ `template <class K, class V> py_dict_get_default(...)` と `dict<str, V>` 用の thin sugar が残っている。
- これらは `find/contains + default` へ callsite 側で展開でき、runtime convenience として持つ必要が薄い。

目的:
- 汎用 `py_dict_get_default` を checked-in callsite から外し、不要なら `py_runtime.h` から削除する。

対象:
- `py_dict_get_default(const dict<K, V>&, ...)`
- `py_dict_get_default(const dict<str, V>&, ...)`

非対象:
- `dict<str, str>` 専用 overload
- `JsonObj.get_*`

受け入れ基準:
- checked-in callsite が棚卸しされている。
- representative callsite が explicit lookup へ置換されるか、未使用が確定している。
- helper が削除され、inventory guard が追加される。

確認コマンド:
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py -k dict_get`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `python3 tools/check/check_todo_priority.py`

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01] 汎用 `py_dict_get_default` を最終退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01-S1-02] explicit lookup 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01-S2-02] helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-FINAL-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: `py_runtime.h` 縮小の next slice として、汎用 `py_dict_get_default` convenience を切り出して扱う。boxing/unboxing 本体にはまだ入らない。
- 2026-03-09: checked-in source を棚卸しすると、`py_dict_get_default(` の direct callsite は helper 自身と regression guard だけで、representative 置換対象は存在しなかった。`S2-01` は no-op 完了として扱う。
- 2026-03-09: `find/contains + default` は caller 側で容易に展開できるため、`dict<K, V>` と `dict<str, V>` 用の 3 overload は互換維持価値が薄いと判断し、inventory guard を追加したうえで削除する。
