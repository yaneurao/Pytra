<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-dict-str-node-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `dict<str, str>` 用 `dict_get_node` 縮退

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `dict_get_node(dict<str, str>, ...)` は `str/char*` 組み合わせごとに複数 overload が残っている。
- object-heavy debt ほど大きくはないが、薄い convenience が積み上がっている。

目的:
- `dict<str, str>` node convenience を最小 wrapper に整理し、重複 overload を減らす。

非対象:
- `dict<str, object>` decode helper
- generic dict primitive

受け入れ基準:
- `dict<str, str>` 専用 `dict_get_node` overload が縮退する。
- checked-in codegen / runtime は最小 wrapper で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`

## 1. 方針

1. `dict<str, str>` helper を generic dict / typed helper へ近づける。
2. `char*` / `str` wrapper の重複を減らす。
3. object / JSON debt とは別の小物 cleanup として扱う。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01] `dict<str, str>` 用 `dict_get_node` overload を縮退する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-02] 残す最小 wrapper を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-01] redundant overload を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-02] representative tests を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S3-01] docs / archive を同期する。

## 3. 決定ログ

- 2026-03-08: 本計画は object debt ではなく、typed string-dict convenience の薄い重複整理として扱う。
- 2026-03-08: checked-in production/runtime callsite を棚卸しした結果、`dict_get_node(dict<str, str>, ...)` は definition 以外に残っていなかった。canonical overload は `const str& key, const str& defval` 1 本だけ残し、`const char*` / mixed wrapper は暗黙 `str` 変換へ寄せてよいと判断した。
