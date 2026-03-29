<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-dyn-range-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-dyn-range-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-dyn-range-retirement.md`

# P0: C++ `py_runtime.h` `py_dyn_range_*` 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DYNRANGE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)

背景:
- `py_dyn_range_iter` / `py_dyn_range_view` / `py_dyn_range` は dynamic iterable を range-for へつなぐ compat lane である。
- static typing / typed iterable 正本化の流れでは、これは permanent API ではない。

目的:
- dynamic range wrapper を削減し、typed iterable / explicit adapter へ寄せる。

非対象:
- typed iterable の range-for
- `begin/end(object)` の ADL 補助

受け入れ基準:
- `py_dyn_range_*` が縮退または削除される。
- checked-in code は typed iterable で成立する。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -v`

## 1. 方針

1. checked-in `py_dyn_range` callsite を棚卸しする。
2. typed list / dict / set / str iteration へ置換できるものを先に寄せる。
3. primitive bridge より高位の compat wrapper なので、残さない前提で進める。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01] `py_dyn_range_*` compat wrapper を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-01] `py_dyn_range` callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-02] typed iterable への置換順序を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-02] `py_dyn_range_*` を削除または最小化する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S3-01] guard / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: dynamic range wrapper は typed iterable の代用品としてのみ残っている debt とみなす。
- 2026-03-08: checked-in `py_dyn_range(...)` callsite は (a) generated runtime helper `contains/json/pathlib/re/png/gif/assertions`, (b) `CppEmitter.stmt` の object for-loop lowering, (c) runtime smoke / bridge regression の 3 群に分かれることを確認した。`py_runtime.h` 自身の `py_dyn_range(const object&)` / template wrapper は別扱いで、まず callsite 側を typed iterable へ寄せる。
- 2026-03-08: 置換順序は `generated built_in helper (contains/json) -> generated std/utils helper (pathlib/re/png/gif/assertions) -> emitter stmt runtime-for lowering -> runtime smoke/inventory` とし、非 iterable fail-fast の確認は最後まで `py_dyn_range` 側へ残してよいと固定した。
- 2026-03-08: representative callsite の first slice として `CppEmitter.stmt` の object/runtime for-loop lowering を `py_dyn_range(expr)` から `object __iter_obj = <null-guarded py_iter_or_raise()>; while (true) { optional<object> __next = <null-guarded py_next_or_stop()>; ... }` へ切り替えた。typed iter fastpath は維持し、tuple/object target の representative bridge test も explicit iter/next 期待へ更新した。
- 2026-03-08: `contains/json/pathlib/re/png/gif/assertions` を `--emit-runtime-cpp` で再生成し、`py_runtime.h` から `py_dyn_range_iter` / `py_dyn_range_view` / `py_dyn_range(...)` を削除した。runtime smoke は explicit `py_iter_or_raise()/py_next_or_stop()` へ切り替え、inventory guard を removed signature 前提へ反転した。
- 2026-03-08: 再生成で露出した regressions は `(a) utils/assertions.py` の no-op assignment、`(b) bytes(list)` ctor の ref-first/value-list adapter 漏れ、`(c) typed runtime for-loop target が body 内で stack/value list local 扱いされない` の 3 件だった。`py_assert_stdout` の no-op を source から削除し、`bytes/bytearray` ctor は value-list copy adapter、typed `ForCore` loop target は body scope だけ stack/value list local として扱う補強で解消した。
- 2026-03-08: representative verification は `test_cpp_runtime_iterable.py`, `test_east3_cpp_bridge.py`, `test_py2cpp_codegen_issues.py`, `test_pylib_json.py`, fixture parity `cases=3 pass=3 fail=0`, sample parity `cases=18 pass=18 fail=0` を通した。
