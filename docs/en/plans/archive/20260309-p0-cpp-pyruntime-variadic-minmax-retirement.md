<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-variadic-minmax-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-variadic-minmax-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-variadic-minmax-retirement.md`

# P0: C++ `py_runtime.h` variadic `py_min` / `py_max` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-cpp-pyruntime-template-slimming.md](./archive/20260308-p1-cpp-pyruntime-template-slimming.md)

背景:
- `py_runtime.h` には variadic `py_min(a, b, c, ...)` / `py_max(a, b, c, ...)` wrapper が残っている。
- 2 引数版 `py_min` / `py_max` はすでに generated helper lane へ移っている。
- variadic wrapper も高水準 sugar であり、runtime core へ残す理由が薄い。

目的:
- variadic `py_min` / `py_max` を `py_runtime.h` から外し、generated helper または explicit fold に寄せる。

非対象:
- 2 引数版 `py_min` / `py_max`
- `sum` / `sorted` など他 helper の整理
- arithmetic primitive の core semantics

受け入れ基準:
- `py_runtime.h` から variadic `py_min` / `py_max` が消える。
- representative callsite は generated helper または explicit fold に置換される。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. variadic `py_min` / `py_max` の checked-in callsite を棚卸しし、explicit fold と helper lane のどちらが自然かを決める。
2. representative callsite を置換してから variadic wrapper を削除する。
3. 2 引数版 helper は既存 lane のまま維持し、責務を混ぜない。

## 2. フェーズ

### Phase 1: 棚卸し
- variadic wrapper の checked-in callsite を固定する。

### Phase 2: 置換
- representative callsite を explicit fold または helper lane に置換する。

### Phase 3: 退役
- wrapper を削除し、guard / parity / archive を更新する。

## 3. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01] variadic `py_min` / `py_max` を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S1-02] fold 置換方針と non-goal を決定ログに固定する。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S2-02] regression / inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S3-01] `py_runtime.h` から variadic wrapper を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-VARIADIC-MINMAX-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は variadic wrapper のみを対象とし、2 引数版 `py_min` / `py_max` helper lane は非対象とする。
- 2026-03-09: checked-in source を棚卸しすると、variadic `py_min` / `py_max` の direct callsite は `test_cpp_runtime_iterable.py` の 3 引数 smoke だけで、runtime / emitter / generated C++ には残っていなかった。
- 2026-03-09: helper lane は増やさず、2 引数版 generated helper をネストした explicit fold (`py_min(py_min(a, b), c)`) を canonical 置換にする。
