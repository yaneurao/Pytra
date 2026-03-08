# P0: C++ `py_runtime.h` generic `py_dict_get_default` overload 縮退

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `py_dict_get_default` には `K/V` generic, `char*`, `str`, `std::string`, `optional<dict<...>>`, convertible default など多くの overload がある。
- この多くは codegen convenience であり、runtime core の必須 primitive ではない。
- overload の組み合わせが `py_runtime.h` の行数と可読性を強く圧迫している。

目的:
- generic `py_dict_get_default` を最小 set に整理し、文字列 key wrapper と convertible default wrapper を減らす。

非対象:
- `dict<str, object>` 専用 `py_dict_get_default`
- `JsonObj.get_*()` API

受け入れ基準:
- generic `py_dict_get_default` の overload 数が減る。
- backend / generated code は最小 wrapper で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`

## 1. 方針

1. `dict<K, V>` と `dict<str, V>` の truly required primitive を残す。
2. `str` / `std::string` / `char*` wrapper の重複を減らす。
3. convertible default overload は callsite が薄い wrapper で済むなら削る。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01] generic `py_dict_get_default` overload を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-01] generic overload の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-02] 残す primitive wrapper を決定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-01] redundant overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-02] codegen / runtime tests を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S3-01] parity / docs / archive を同期する。

## 3. 決定ログ

- 2026-03-08: 本計画は generic dict primitive の全廃ではなく、wrapper 重複の縮退に焦点を当てる。
