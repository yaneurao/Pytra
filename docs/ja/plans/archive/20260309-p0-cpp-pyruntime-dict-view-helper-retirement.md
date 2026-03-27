<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-dict-view-helper-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01] `py_dict_keys` / `py_dict_values` を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-01] checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-02] 置換順序と non-goal を決定ログに固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-01] representative callsite を generated helper または explicit loop に置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-02] regression / inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-01] `py_runtime.h` から helper を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は dict view helper の高水準 sugar だけを対象とし、dict primitive と object carrier 本体は非対象とする。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-01]: checked-in callsite は `cpp_emitter.py` の `DictKeys` / `DictValues` 描画と、それを固定する `test_east3_cpp_bridge.py` / `test_py2cpp_codegen_issues.py` だけだった。generated runtime / built_in / selfhost に direct callsite は無かった。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S1-02]: helper artifact を増やさず、C++ emitter の `DictKeys` / `DictValues` を module-local lambda へ展開する方針に固定した。`dict.items()` は既存どおり owner dict をそのまま返し、`dict` primitive と object carrier 本体は non-goal に維持する。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-01]: `cpp_emitter._render_dict_view_expr()` を追加し、`dict[K, V]` の owner 型から `list<K>` / `list<V>` を決めて explicit loop を描画するようにした。`pyobj` list model でも `_cpp_list_value_model_type_text()` を使って `list<str>` / `list<int64>` を返す。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S2-02]: regression は `test_east3_cpp_bridge.py` の `DictKeys` / `DictValues` 期待値を lambda fragment ベースに更新し、`test_py2cpp_codegen_issues.py` に `rc_list_from_value(([&]() -> list<...>` の codegen 断片を固定、`test_cpp_runtime_iterable.py` に generic `py_dict_keys` / `py_dict_values` signature の `NotIn` guard を追加した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-01]: `py_runtime.h` から `template <class K, class V> py_dict_keys(const dict<K, V>&)` と `py_dict_values(const dict<K, V>&)` を削除した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTVIEW-01-S3-02]: verification は `test_east3_cpp_bridge.py`、`test_py2cpp_codegen_issues.py -k dynamic_dict_values`、`test_cpp_runtime_iterable.py`、fixture parity `cases=3 pass=3 fail=0` を通した。
