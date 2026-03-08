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
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `python3 tools/check_todo_priority.py`

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01] `py_dict_items` sugar を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S1-02] explicit loop 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S2-02] helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTITEMS-01-S3-01] guard / docs / archive を更新する。

## 決定ログ

- 2026-03-09: `py_runtime.h` の高水準 dict sugar をさらに減らす tranche として `py_dict_items` を分離した。
