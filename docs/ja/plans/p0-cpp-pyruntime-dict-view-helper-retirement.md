# P0: C++ `py_runtime.h` `py_dict_keys` / `py_dict_values` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTVIEW-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-cpp-pyruntime-template-slimming.md](./archive/20260308-p1-cpp-pyruntime-template-slimming.md)

背景:
- `py_runtime.h` には `py_dict_keys(const dict<K, V>&)` と `py_dict_values(const dict<K, V>&)` が残っている。
- これは low-level runtime core ではなく、高水準 collection helper である。
- `dict` view helper は generated `built_in` または linked helper artifact 側へ寄せた方が、`py_runtime.h` の責務が明確になる。

目的:
- `py_dict_keys` / `py_dict_values` を `py_runtime.h` から外し、checked-in callsite を generated helper 側へ寄せる。

非対象:
- `dict` primitive (`py_at`, `py_set_at`)
- object-based dynamic dict helper の再導入
- `dict_items` helper の復活

受け入れ基準:
- `py_runtime.h` から `py_dict_keys` / `py_dict_values` が消える。
- checked-in callsite は generated helper または explicit loop に置換される。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. checked-in callsite を棚卸しし、generated helper へ寄せられる箇所と explicit loop 化が必要な箇所を分ける。
2. 既存 `built_in` helper へ寄せられるものから先に置換し、`py_runtime.h` から sugar を削除する。
3. runtime core に dict view helper を再配置しない。

## 2. フェーズ

### Phase 1: 棚卸し
- `py_dict_keys` / `py_dict_values` の checked-in callsite を固定する。

### Phase 2: 置換
- representative callsite を generated helper または explicit loop へ置換する。

### Phase 3: 退役
- helper を削除し、inventory guard / parity / archive を更新する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01] `py_dict_keys` / `py_dict_values` を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-02] 置換順序と non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-01] representative callsite を generated helper または explicit loop に置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-01] `py_runtime.h` から helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は dict view helper の高水準 sugar だけを対象とし、dict primitive と object carrier 本体は非対象とする。
