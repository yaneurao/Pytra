# P0: C++ `py_runtime.h` `dict_get_*` convenience 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `dict_get_bool/str/int/float/list/node` は `dict<str, object>` decode convenience として残っている。
- これは `JsonObj.get_*()` と役割が重なり、runtime core を厚くしている。

目的:
- `dict_get_*` を `JsonObj.get_*()` または typed helper に吸収し、`py_runtime.h` から退役する。

非対象:
- `dict<str, str>` 用 `dict_get_node`
- generic dict primitive

受け入れ基準:
- `dict_get_bool/str/int/float/list/node(dict<str, object>, ...)` が消える。
- JSON/selfhost decode は `JsonObj.get_*()` で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`

## 1. 方針

1. object-dict decode convenience を `JsonObj` nominal API に吸収する。
2. `dict_get_list/node` も explicit nominal decode に寄せる。
3. `dict<str, str>` 専用 helper はこの tranche では別扱いにする。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01] `dict_get_*` convenience を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-01] `dict_get_*` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-02] `JsonObj` API への置換表を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-01] representative callsite / tests を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-02] `dict_get_*` convenience を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S3-01] guard / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: `dict_get_*` は JSON nominal API 導入後の一時 convenience であり、runtime core の恒久 surface と見なさない。
