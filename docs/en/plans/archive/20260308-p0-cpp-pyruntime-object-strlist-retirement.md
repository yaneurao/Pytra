<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-object-strlist-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-strlist-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-strlist-retirement.md`

# P0: C++ `py_runtime.h` `py_to_str_list_from_object` 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_to_str_list_from_object` は `object` に入った list を `list<str>` に戻す convenience helper である。
- argv / JSON / selfhost decode が typed lane に寄るほど、これは object bridge の小さな残骸になる。

目的:
- `py_to_str_list_from_object` を退役し、typed argv / decode helper を正本にする。

非対象:
- typed `py_runtime_argv`
- generic `py_to<list<T>>(object)` 全体

受け入れ基準:
- `py_to_str_list_from_object` の checked-in callsite が消える。
- helper 自体が削除または private 化される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py' -v`

## 1. 方針

1. argv / selfhost decode の callsite を棚卸しする。
2. typed `list<str>` lane に寄せる。
3. generic conversion machinery には手を入れず、専用 convenience だけを落とす。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01] `py_to_str_list_from_object` を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-01] callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-02] typed argv / decode 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-02] helper を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S3-01] parity / docs / archive を更新する。

## 3. 決定ログ

- 2026-03-08: 専用 `str list` convenience は generic conversion machinery と切り分けて扱う。
- 2026-03-08: checked-in runtime callsite は `argparse.parse_args(argv)` のみで、`argv: Any` を維持しつつ generated C++ は `py_to<rc<list<str>>>(argv)` を経由する形へ寄せた。`list<T>(rc<list<T>>)` ctor を追加し、専用 helper を戻さずに `list<str>` local へ受けられるようにした。
- 2026-03-08: emitter 側に残っていた `py_to_str_list_from_object(...)` 呼び出しは `list<str>(expr)` lane へ置換した。`object` / `rc<list<str>>` / `list<str>` を同じ coercion surface で吸えるため、専用 `str list` helper を再導入せずに representative codegen / fixture parity を通せる。
