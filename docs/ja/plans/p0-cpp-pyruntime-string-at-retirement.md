# P0: C++ `py_runtime.h` `py_at(str, idx)` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-STRAT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-cpp-py-runtime-core-slimming.md](./archive/20260308-p1-cpp-py-runtime-core-slimming.md)

背景:
- `py_runtime.h` には `py_at(const str&, int64)` が残っている。
- これは string helper の一部であり、runtime core より string helper lane に置く方が自然である。
- 既に `py_join` / `py_split` / `py_count` など string helper は generated `built_in/string_ops` へ移っている。

目的:
- `py_at(str, idx)` を `py_runtime.h` から外し、string helper lane または explicit expression に寄せる。

非対象:
- list / dict の `py_at`
- string slicing 全体の設計変更
- object carrier の string unboxing

受け入れ基準:
- `py_runtime.h` から `py_at(const str&, int64)` が消える。
- representative callsite は string helper lane または direct expression で通る。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. `py_at(str, idx)` の checked-in callsite を棚卸しし、direct expression 化と helper 化のどちらが自然かを決める。
2. representative callsite を先に置換し、inventory guard を追加する。
3. string index sugar は runtime core に戻さない。

## 2. フェーズ

### Phase 1: 棚卸し
- `py_at(str, idx)` 依存箇所と置換候補を固定する。

### Phase 2: 置換
- representative callsite を string helper lane または direct expression に置換する。

### Phase 3: 退役
- helper を削除し、guard / parity / archive を更新する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01] `py_at(str, idx)` を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S1-02] direct expression と helper lane の使い分けを決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S3-01] `py_runtime.h` から helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-STRAT-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は string index helper の退役だけを対象とし、slice helper や string object 本体は非対象とする。
