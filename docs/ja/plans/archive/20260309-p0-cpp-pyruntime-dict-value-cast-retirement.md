<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-dict-value-cast-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `py_dict_value_cast` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` には `py_dict_value_cast(const object&)`, `py_dict_value_cast(const char*)`, `py_dict_value_cast(const U&)` が残っている。
- これは dict write (`py_at(dict<K, V>&, ...)`, `py_set_at(dict<K, V>&, ...)`) の value 正規化を helper 側へ押し込んだ sugar で、dict value の typed 化ポリシーが callsite から読めない。
- `py_dict_key_cast` は既に削除済みであり、value 側だけ helper 名が残るのは責務分離として不均衡である。

目的:
- `py_dict_value_cast` を `py_runtime.h` から除去し、dict value の typed 化を `py_to<V>(...)` や explicit conversion へ寄せる。
- dict write の挙動を helper 名に依存せず読めるようにする。

非対象:
- `py_to<T>(object)` 本体の再設計
- dict primitive 自体の削除
- `JsonObj` decode helper の変更

受け入れ基準:
- `py_runtime.h` から `py_dict_value_cast` 3 本が削除される。
- runtime / emitter / generated 側の checked-in caller が explicit conversion に置換される。
- representative C++ runtime / backend test が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. `py_dict_value_cast` の checked-in callsite を棚卸しし、runtime 内 helper に閉じているか、外部 caller があるかを固定する。
2. dict value の typed 化は `py_to<V>(...)` または explicit literal construction に置換する。
3. value conversion policy を helper 名へ再抽象化しない。

## 2. フェーズ

### Phase 1: 棚卸し
- `py_dict_value_cast` 依存箇所を列挙し、置換順序を決める。

### Phase 2: 置換
- representative path を explicit conversion に置換する。
- regression / inventory guard を追加する。

### Phase 3: 退役
- helper を削除し、parity / docs / archive を更新する。

## 3. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01] `py_dict_value_cast` を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S1-01] `py_dict_value_cast` の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S1-02] dict value conversion の canonical rule を決定ログに固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S2-01] representative callsite を explicit conversion へ置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S2-02] regression / inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S3-01] `py_runtime.h` から `py_dict_value_cast` を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTVALUECAST-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は value cast helper 名の退役のみを対象にし、dict primitive や `py_to<T>(object)` の大規模再設計は非対象とする。
- 2026-03-09: checked-in `py_dict_value_cast(...)` callsite は `src/runtime/cpp/native/core/py_runtime.h` 内の `py_at(dict<K, V>&, ...)`, `py_at(const dict<K, V>&, ...)`, `py_set_at(dict<K, V>&, ...)` だけで、generated runtime / emitter / tests / sample からの direct use は存在しなかった。
- 2026-03-09: canonical rule は helper 名を残さず、dict key/value coercion を `py_at/py_set_at` 内の local conversion expression に直接展開する形へ固定した。`object`, `const char*`, same-type, convertible, fallback-constructor の既存挙動は維持する。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から `py_dict_value_cast` 3 本を削除し、`test_cpp_runtime_iterable.py` に removed inventory guard を追加した。
- 2026-03-09: verification は `test_cpp_runtime_iterable.py`, `test_east3_cpp_bridge.py`, `tools/runtime_parity_check.py --targets cpp --case-root fixture`, `tools/check_todo_priority.py`, `git diff --check` を基準とする。
