# P0: C++ `py_runtime.h` `dict<str, str>` default sugar 最終退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [src/runtime/cpp/native/core/py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h)

背景:
- `dict<str, str>` 専用の `py_dict_get_default(..., const char*)` 2 本がまだ残っている。
- これは convenience として薄く、checked-in callsite が限定的なら explicit lookup に寄せられる。

目的:
- `dict<str, str>` default sugar を棚卸しし、不要なら削除する。

対象:
- `py_dict_get_default(const dict<str, str>&, const char*, const char*)`
- `py_dict_get_default(const dict<str, str>&, const str&, const char*)`

非対象:
- `dict<str, V>` 汎用 overload
- `JsonObj` API

受け入れ基準:
- checked-in callsite が明確になっている。
- helper を削除できるか、残置理由が固定されている。
- inventory guard が更新される。

確認コマンド:
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `python3 tools/check_todo_priority.py`

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01] `dict<str, str>` default sugar を最終整理する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01-S1-02] 削除可否を決定ログへ固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01-S2-01] representative callsite を explicit lookup へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01-S2-02] helper を削除または残置理由を確定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-DEFAULT-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: `dict_get_node(dict<str, str>)` 退役後に残る `dict<str, str>` sugar の最終 tranche として分離した。
