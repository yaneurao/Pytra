# P0: C++ `py_runtime.h` `optional<dict<...>>` `py_dict_get` compat 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- [py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h) には `py_dict_get(const ::std::optional<dict<K, V>>&, ...)` と `py_dict_get(const ::std::optional<dict<str, V>>&, const char*)` が残っている。
- これは optional owner を runtime helper が吸って `out_of_range` を投げる compat lane であり、callsite 側の `if d is None` / explicit unwrap と責務が二重化している。
- decode-first / explicit branch 方針では、`optional` の null handling は呼び出し側で表現し、`py_runtime.h` には typed dict access の本体だけを残す方がよい。

目的:
- `optional<dict<...>>` 向け `py_dict_get` helper の checked-in callsite を棚卸しし、callsite 側 explicit unwrap へ寄せる。
- `py_runtime.h` から optional overload を削除する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の optional dict `py_dict_get`
- C++ emitter / generated runtime / checked-in sample の representative callsite

非対象:
- `py_dict_get_default` の optional/default lane
- `optional<dict<...>>` 自体の language support

受け入れ基準:
- optional dict `py_dict_get` の checked-in callsite が棚卸しされている。
- representative callsite が explicit unwrap へ置換されている。
- helper が削除され、regression と parity が green である。

確認コマンド:
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_east3_cpp_bridge.py`
- `PYTHONPATH=src python3 test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し

- checked-in callsite を棚卸しし、emitter 生成式と runtime/generated helper を分けて記録する。
- null handling を callsite 側へ寄せるときの expression pattern を決める。

### Phase 2: 置換

- representative callsite を `if/contains` / ternary / lambda など explicit unwrap へ置換する。
- codegen expectation と runtime smoke を更新する。

### Phase 3: helper 削除

- `py_runtime.h` から optional dict `py_dict_get` overload を削除する。
- docs / archive を同期する。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01] `optional<dict<...>>` `py_dict_get` compat を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01-S1-01] optional dict `py_dict_get` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01-S1-02] explicit unwrap 置換パターンを固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01-S2-02] helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-DICTGET-01-S3-01] regression / parity / docs / archive を更新する。

## 決定ログ

- 2026-03-09: 起票時点では `optional<dict<...>>` の `py_dict_get` overload だけを対象にし、`py_dict_get_default` の default-return lane は別タスクとして分ける。null handling は runtime helper ではなく callsite 側 explicit branch を正本にする。
