# P0: C++ `py_runtime.h` `py_dict_key_cast` 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- `py_runtime.h` には `py_dict_key_cast(const object&)`, `py_dict_key_cast(const char*)`, `py_dict_key_cast(const Q&)` が残っている。
- これは dict key を runtime helper 側で暗黙変換する layer で、typed key と decode-first を曖昧にする。
- `object key` compat を削った後も helper 自体が残っているため、今後の callsite が再び暗黙 lane に戻る余地がある。

目的:
- dict key は callsite で明示的に `str(...)` または typed key へ正規化し、`py_dict_key_cast` を `py_runtime.h` から除去する。

非対象:
- dict value cast
- `py_dict_get` / `py_dict_get_default` 本体の意味変更
- `JsonObj` 専用 decode helper

受け入れ基準:
- `py_runtime.h` から `py_dict_key_cast` 一式が消える。
- C++ emitter / runtime callsite は key 型を明示的に構築してから dict helper を呼ぶ。
- representative fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. `py_dict_key_cast` の checked-in callsite を棚卸しし、emitter / runtime どちらが暗黙 key cast に依存しているかを固定する。
2. key normalization は callsite 側へ押し戻し、helper から key-conversion policy を外す。
3. helper 削除後に同等の convenience を別名で再導入しない。

## 2. フェーズ

### Phase 1: 棚卸し
- `py_dict_key_cast` 依存箇所を列挙し、置換順序を固定する。

### Phase 2: 置換
- representative path を typed key construction へ置換する。

### Phase 3: 退役
- helper を削除し、regression / parity / docs を閉じる。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01] `py_dict_key_cast` を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S1-01] `py_dict_key_cast` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S1-02] key normalization の新ルールと non-goal を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S2-01] representative callsite を explicit key construction へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S3-01] `py_dict_key_cast` を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTKEYCAST-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は dict key の暗黙 cast policy を helper から除去する。dict value cast や generic `py_to<T>(object)` は本計画の対象外とする。
