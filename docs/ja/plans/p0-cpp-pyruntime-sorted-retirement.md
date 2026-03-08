# P0: C++ `py_runtime.h` `sorted` helper 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-SORTED-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-cpp-pyruntime-template-slimming.md](./archive/20260308-p1-cpp-pyruntime-template-slimming.md)
- [archive/20260308-p2-linked-runtime-helper-template-v1.md](./archive/20260308-p2-linked-runtime-helper-template-v1.md)

背景:
- `py_runtime.h` には `sorted(const list<T>&)` と `sorted(const set<T>&)` が残っている。
- これは generic high-level helper であり、`@template` helper や linked helper artifact と相性がよい。
- `sum/min/max/zip` を外へ出した流れと同じ種類の整理対象である。

目的:
- `sorted` helper を `py_runtime.h` から外し、generated helper または linked helper lane に寄せる。

非対象:
- `list.sort()` / `py_list_sort_mut`
- object list sort の dynamic fallback
- comparison semantics 自体の変更

受け入れ基準:
- `py_runtime.h` から `sorted(const list<T>&)` / `sorted(const set<T>&)` が消える。
- representative callsite は helper lane へ移る。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. checked-in callsite を棚卸しし、generated `built_in` helper 化か linked helper artifact 化かを決定する。
2. representative callsite を helper lane に寄せてから、`py_runtime.h` の sugar を削除する。
3. runtime core に `sorted` helper を戻さない。

## 2. フェーズ

### Phase 1: 棚卸し
- `sorted` helper の checked-in callsite と helper lane 候補を固定する。

### Phase 2: 置換
- representative callsite を helper lane に置換する。

### Phase 3: 退役
- helper を削除し、guard / parity / archive を更新する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01] `sorted` helper を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S1-02] helper lane と non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S2-01] representative callsite を helper lane に置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S3-01] `py_runtime.h` から helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-SORTED-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は `sorted` の高水準 helper だけを扱い、`list.sort()` や object-list dynamic sort lane は非対象とする。
