<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-dictget-string-sugar-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `py_dict_get(dict<str, V>)` string sugar 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- `py_runtime.h` には `py_dict_get(const dict<str, V>&, const char*)` / `const str&` / `const ::std::string&` の 3 本が残っている。
- これは key を `str` に正規化せずに convenience で吸収する layer であり、decode-first と explicit key normalization の方針に反する。
- 既に `object key` compat は削除済みで、残る sugar も emitter / callsite 側で `str(...)` 正規化すれば不要になる。

目的:
- `dict<str, V>` の key access は `str` へ正規化した callsite と generic `py_dict_get(dict<K, V>, const K&)` を正本にし、string sugar overload を退役する。

非対象:
- generic `py_dict_get(dict<K, V>, const K&)`
- `py_dict_get_default`
- `JsonObj.get_*()` 自体の API 再設計

受け入れ基準:
- `py_runtime.h` から `py_dict_get(const dict<str, V>&, const char*)` / `const str&` / `const ::std::string&` の sugar overload が消える。
- representative C++ codegen は key を `str(...)` か typed `str` local に正規化してから dict access する。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. 先に checked-in callsite を棚卸しし、`const char*` / `std::string` key の発生地点を固定する。
2. emitter / runtime helper 側で key を `str` へ明示正規化し、sugar overload 依存を消してから helper を削除する。
3. `lowered_kind` 特例など既存の missing-key behavior は generic `str` lane に集約し、別の compat helper は増やさない。

## 2. フェーズ

### Phase 1: 棚卸し
- checked-in runtime / emitter / generated callsite で string sugar overload に依存する場所を固定する。

### Phase 2: 置換
- `char*` / `std::string` key を `str` に正規化するよう callsite を更新する。

### Phase 3: 退役
- string sugar overload を削除し、inventory guard / parity / docs を更新する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01] `py_dict_get(dict<str, V>)` string sugar を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S1-01] `const char*` / `std::string` key sugar の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S1-02] key 正規化順序と non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S2-01] representative callsite を `str` 正規化へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S2-02] regression と inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S3-01] string sugar overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は key normalization convenience の撤去だけを扱い、missing-key behavior 変更や dict default helper の再設計は対象外とする。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S1-01]: checked-in callsite を棚卸しした結果、production で `const char*` / `std::string` key sugar に依存しているのは `src/runtime/cpp/generated/built_in/type_id.cpp` の `py_dict_get(_TYPE_STATE, "next_user_type_id")` と、`cpp_emitter.py` が dict subscript を `py_dict_get({val}, {idx})` と描画した先で `idx` が `char*` / `std::string` になる経路だった。JSON runtime や object-dict compat lane は既に別トラックで削除済みで、今回の対象は generic `dict<str, V>` sugar に限定できる。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S1-02]: 削除順序は `generated built_in/type_id.cpp` の literal key を `str("next_user_type_id")` へ正規化 -> C++ emitter の dict key coercion 結果を `str` に固定 -> regression / inventory guard 更新 -> sugar overload 削除、とする。`lowered_kind` 特例や generic `dict<K, V>` 本体は non-goal のまま維持する。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S2-01]: `cpp_emitter._coerce_dict_key_expr()` の `dict[str, V]` key coercion は `py_to_string(...)` ではなく `str(...)` を返すように変更し、dict pop/get/maybe など `_coerce_dict_key_expr()` を通る全経路を generic `py_dict_get(dict<K, V>, const K&)` に合わせた。checked-in `type_id.cpp` も `str("next_user_type_id")` へ更新した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S2-02]: regression は `test_east3_cpp_bridge.py` の dict key coercion 期待値を `str(k)` へ更新し、`test_cpp_runtime_iterable.py` に `py_dict_get(const dict<str, V>&, const char*) / const str& / const ::std::string&` の removed inventory guard を追加した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-DICTGET-STRING-SUGAR-01-S3-01]: `py_runtime.h` から `py_dict_get(const dict<str, V>&, const char*)`, `const str&`, `const ::std::string&` を削除した。`lowered_kind` 特例つき missing-key diagnostics は generic `dict<K, V>` lane に移さず、本 tranche では convenience 削除を優先した。
