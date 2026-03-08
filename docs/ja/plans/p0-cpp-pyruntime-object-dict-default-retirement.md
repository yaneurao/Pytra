# P0: C++ `py_runtime.h` `dict<str, object>` 専用 `py_dict_get_default` 縮退

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- `dict<str, object>` 専用 `py_dict_get_default` は `object`, `char*`, `str`, `dict<str, object>`, template default まで広がっている。
- `JsonObj.get_*()` が進むほど、これらは JSON convenience debt になる。

目的:
- object-dict 専用 default access を `JsonObj` decode helper に寄せ、runtime 本体から減らす。

非対象:
- generic `dict<K, V>` primitive
- typed `dict<str, V>` default access

受け入れ基準:
- `dict<str, object>` 専用 `py_dict_get_default` の多くが削除される。
- JSON decode は `JsonObj.get_*` で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`

## 1. 方針

1. JSON decode helper へ寄せられるものを優先して削る。
2. `object` default を返す helper を permanent API と見なさない。
3. どうしても残るなら `JsonObj` private/helper 側へ寄せる。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01] `dict<str, object>` 専用 `py_dict_get_default` を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-01] object-dict default access の callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-02] `JsonObj.get_*` へ寄せる順序を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-01] representative callsite を `JsonObj` helper へ移す。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-02] object-dict default overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S3-01] regression / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: object-dict default access は generic dict primitive とは別 debt として管理する。
