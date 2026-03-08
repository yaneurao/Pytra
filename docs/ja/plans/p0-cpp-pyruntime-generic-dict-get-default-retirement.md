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
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-01] generic overload の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-02] 残す primitive wrapper を決定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-01] redundant overload を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-02] codegen / runtime tests を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S3-01] parity / docs / archive を同期する。

## 3. 決定ログ

- 2026-03-08: 本計画は generic dict primitive の全廃ではなく、wrapper 重複の縮退に焦点を当てる。
- 2026-03-08: checked-in production/backend callsite を棚卸しした結果、current C++ emitter は typed `dict.get(key, default)` を `owner_expr.get(key_expr, default_expr)` へ直接 lower しており、`py_dict_get_default(...)` generic wrapper を使っていなかった。checked-in で generic overload に依存していたのは selfhost artifact `selfhost/runtime/cpp/pytra-gen/compiler/east_parts/core.cpp` のみで、形は主に `(a) dict<int64, tuple<...>> + same-type default` と `(b) dict<str, str> + str key + const char* default` だった。
- 2026-03-08: 上記棚卸しを受けて、残す primitive は `dict<K, V> + K + const V&` と `dict<str, V> + {const char*, str} + const V&`、および selfhost artifact 互換の最小 special-case として `dict<str, str> + {const char*, str} + const char*` に固定する。削除対象は `optional<dict<...>>` wrapper、`::std::string` key wrapper、`template<class D>` convertible default wrapper 一式とする。
- 2026-03-08: `src/runtime/cpp/native/core/py_runtime.h` から `optional<dict<...>>` wrapper、`dict<str, V> + ::std::string key` wrapper、generic convertible default wrapper 一式を削除した。selfhost artifact がまだ必要としている `dict<str, str> + const char* default` だけは dedicated overload へ狭めて残した。
- 2026-03-08: `test_cpp_runtime_iterable.py` には removed signature guard を追加し、`dict<str, str> + const char* default` special-case のみ `In` で固定した。representative verification は `test_cpp_runtime_iterable.py`、`test_py2cpp_codegen_issues.py`、fixture parity `cases=3 pass=3 fail=0` を通した。
