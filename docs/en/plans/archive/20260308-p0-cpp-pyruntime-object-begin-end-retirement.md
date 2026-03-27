<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-object-begin-end-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-begin-end-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-begin-end-retirement.md`

# P0: C++ `py_runtime.h` `begin/end(object)` / ADL 補助 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `begin/end(const object&)`, `pytra::gc::begin/end`, `begin(optional<object>)` は range-for compat のために残っている。
- dynamic iterable 依存を減らすなら、ここは大きい掃除候補である。

目的:
- `object` / `optional<object>` の ADL range-for bridge を退役し、typed iterable へ寄せる。

非対象:
- typed container の `begin/end`
- low-level `PyObj` iterator 本体

受け入れ基準:
- `begin/end(object)` 系が削除または最小化される。
- checked-in sample / selfhost code が typed iteration で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`

## 1. 方針

1. range-for compat callsite を棚卸しする。
2. `py_dyn_range` と連動して typed iterable へ寄せる。
3. ADL 補助は permanent API と見なさず削除前提で進める。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01] `begin/end(object)` と ADL 補助を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-01] range-for compat callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-02] typed iterable 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-02] `begin/end(object)` と ADL 補助を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S3-01] parity / docs / archive を更新する。

## 3. 決定ログ

- 2026-03-08: 本計画は range-for ADL 互換だけを対象にし、iterator primitive の低レベル実装とは切り分ける。
- 2026-03-08: `py_dyn_range` 退役後に checked-in C++ backend/runtime/sample を棚卸しした結果、`begin/end(object)` と `pytra::gc::begin/end(RcHandle<PyObj>)` の明示 callsite は残っていなかった。inventory guard を正本にして定義自体を削除した。
