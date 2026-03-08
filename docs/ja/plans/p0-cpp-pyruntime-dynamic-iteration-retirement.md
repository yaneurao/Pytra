# P0: C++ `py_runtime.h` dynamic iteration bridge 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DYNITER-01`

関連:
- [spec-dev.md](../spec/spec-dev.md)
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `py_iter_or_raise(const object&)` と `py_next_or_stop(const object&)` は `object` iterable を runtime で救済する lane である。
- decode-first / static typing を正本にするなら、`object` のまま iteration するのは compile error に寄せたい。

目的:
- `object` iterable fallback を縮退し、typed iterable と nominal helper を正本にする。

非対象:
- `PyObj` 自体の iterator 実装
- typed list / dict / set / str の iterator

受け入れ基準:
- `py_iter_or_raise(object)` / `py_next_or_stop(object)` の public-ish compat 依存が消える。
- checked-in generated/selfhost code が typed iterable で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`

## 1. 方針

1. `object` iteration callsite を棚卸しして typed / nominal path へ置換する。
2. `py_dyn_range` と `begin/end(object)` は別 tranche で扱い、まず primitive bridge だけを見直す。

## 2. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01] dynamic iteration primitive を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-01] `py_iter_or_raise/object` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-02] typed / nominal 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-02] primitive bridge を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S3-01] parity / docs / archive を更新する。

## 3. 決定ログ

- 2026-03-08: 本計画では dynamic iteration primitive を対象にし、range-for wrapper は別計画へ切り分ける。
