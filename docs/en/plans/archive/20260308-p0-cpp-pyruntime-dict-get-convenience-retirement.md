<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-dict-get-convenience-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-dict-get-convenience-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-dict-get-convenience-retirement.md`

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
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py' -v`

## 1. 方針

1. object-dict decode convenience を `JsonObj` nominal API に吸収する。
2. `dict_get_list/node` も explicit nominal decode に寄せる。
3. `dict<str, str>` 専用 helper はこの tranche では別扱いにする。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01] `dict_get_*` convenience を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-01] `dict_get_*` callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-02] `JsonObj` API への置換表を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-01] representative callsite / tests を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-02] `dict_get_*` convenience を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S3-01] guard / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: `dict_get_*` は JSON nominal API 導入後の一時 convenience であり、runtime core の恒久 surface と見なさない。
- 2026-03-08: checked-in production/backend callsite を棚卸しした結果、`dict_get_bool/str/int/float/list/node(dict<str, object>, ...)` を直接使っているのは `CppEmitter._render_dict_get_default_expr()` の object-dict lane だけだった。runtime / generated JSON helper は `JsonObj.get_*()` と `py_dict_get_default` / typed decode に寄せられており、`dict<str, str>` 専用 `dict_get_node` は非対象として残してよいと判断した。
- 2026-03-08: `CppEmitter._render_dict_get_default_expr()` は object-dict path を `py_dict_get_default(...)` と explicit lambda (`contains/find -> py_to<T>(it->second)`) へ置換し、optional owner と typed list default を runtime convenience なしで描画する形にした。`dict_get_*` に依存していた representative codegen tests も lambda / `py_dict_get_default` 前提へ更新した。
- 2026-03-08: `src/runtime/cpp/native/core/py_runtime.h` から `dict_get_bool/str/int/float/list` と `dict_get_node(dict<str, object>, ...)` を削除し、`test_cpp_runtime_iterable.py` に removed inventory guard を追加した。verification は `test_py2cpp_codegen_issues.py -k dict_get`、`test_cpp_runtime_iterable.py`、`test_pylib_json.py`、`test_py2cpp_features.py -k json`、fixture parity `cases=3 pass=3 fail=0` を通した。
