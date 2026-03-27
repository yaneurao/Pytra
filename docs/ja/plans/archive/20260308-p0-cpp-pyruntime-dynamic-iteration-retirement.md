<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-dynamic-iteration-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01] dynamic iteration primitive を縮退する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-01] `py_iter_or_raise/object` callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-02] typed / nominal 置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-02] primitive bridge を削除または最小化する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S3-01] parity / docs / archive を更新する。

## 3. 決定ログ

- 2026-03-08: 本計画では dynamic iteration primitive を対象にし、range-for wrapper は別計画へ切り分ける。
- 2026-03-08: checked-in callsite は `CppEmitter` の `ObjIterInit` / `ObjIterNext` lowering と runtime smoke に限られていた。`py_dyn_range` / `begin/end(object)` は別 tranche のまま据え置き、primitive bridge だけ method call へ寄せる。
- 2026-03-08: `ObjIterInit` / `ObjIterNext` は null guard 付き lambda から `PyObj::py_iter_or_raise()` / `PyObj::py_next_or_stop()` を直接呼ぶ形へ更新し、`py_runtime.h` の free helper `py_iter_or_raise(const object&)` / `py_next_or_stop(const object&)` は削除した。`py_dyn_range_view` の内部実装も同じ method call に合わせた。
- 2026-03-08: representative verification は `test_east3_cpp_bridge.py`、`test_py2cpp_codegen_issues.py -k any_boundary_builtin_names`、`test_cpp_runtime_iterable.py`、fixture parity `cases=3 pass=3 fail=0`、sample parity `cases=18 pass=18 fail=0` を通した。
