# P0: C++ `py_runtime.h` `py_dict_get_maybe` 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_dict_get_maybe` は Python の `dict.get(key)` 省略形を C++ runtime convenience として広く持っている。
- decode-first 方針では `JsonObj.get_optional` 系か typed `dict.get` lowering を正本にしたい。
- `optional<dict<...>>` や `dict<str, object>` ごとの overload 増殖は `py_runtime.h` を不必要に太らせる。

目的:
- `py_dict_get_maybe` を runtime core の汎用 convenience から外し、JSON / typed dict 側へ寄せる。

非対象:
- explicit default 付き `py_dict_get_default`
- generic dict primitive そのもの

受け入れ基準:
- `py_dict_get_maybe` 系 overload が大幅に減る。
- JSON / selfhost loader は `JsonObj` helper または explicit default へ移行する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*.py' -v`

## 1. 方針

1. `maybe` semantics が本当に必要な callsite を固定する。
2. JSON は `JsonObj.get_*`、typed dict は explicit default / exception へ寄せる。
3. generic dict primitive を壊さず convenience だけを落とす。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01] `py_dict_get_maybe` convenience を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-01] `py_dict_get_maybe` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-02] `JsonObj` / explicit default への移行方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-02] `py_dict_get_maybe` overload を削減する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S3-01] guard / docs / parity を更新する。

## 3. 決定ログ

- 2026-03-08: `maybe` convenience は typed dict primitive ではなく decode helper の都合で残っている debt として扱う。
