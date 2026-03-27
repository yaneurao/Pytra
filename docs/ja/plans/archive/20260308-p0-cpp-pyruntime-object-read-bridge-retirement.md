<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-object-read-bridge-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` object read bridge 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-READ-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- `py_runtime.h` にはまだ `py_at(const object&, int64)` と `py_slice(const object&, ...)` が残っている。
- これは現在の `JsonArr.raw: object` と object-based read bridge の名残であり、decode-first 方針と噛み合わない。
- `JsonArr` が nominal / typed carrier に寄るほど、この helper は permanent API ではなく compat debt になる。

目的:
- `object` をそのまま index / slice する lane を退役し、typed list / str / `JsonArr` accessor を正本にする。

非対象:
- list / str / tuple の typed `py_at`
- `make_object` / `py_to<T>(object)` / `type_id` 本体
- header 分割

受け入れ基準:
- `py_at(const object&, int64)` と `py_slice(const object&, ...)` が `py_runtime.h` から消える。
- JSON runtime と representative sample が typed / `JsonArr` accessor で成立する。
- C++ parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 方針

1. 先に `JsonArr` / generated JSON helper 側の `object` read 依存を棚卸しする。
2. `py_at(object)` / `py_slice(object)` を callsite から除去してから helper を削除する。
3. typed list / str / `JsonArr` accessor 以外の read fallback は増やさない。

## 2. フェーズ

### Phase 1: 棚卸し
- `json.cpp/json.h` と checked-in sample / runtime test の read bridge 依存を固定する。

### Phase 2: 置換
- JSON runtime を typed / nominal carrier へ寄せ、`py_at(object)` / `py_slice(object)` 依存を消す。

### Phase 3: 退役
- helper を削除し、inventory guard と parity を更新する。

## 3. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01] `py_runtime.h` の object read bridge を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-01] `py_at(object)` / `py_slice(object)` の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-02] `JsonArr` 依存と削除順序を決定ログへ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-01] JSON / runtime callsite を typed / nominal accessor へ置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-02] representative regression を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-01] `py_at(object)` / `py_slice(object)` を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-08: 本計画は object collection bridge 第2波として read lane だけを扱い、mutation lane の再導入は認めない。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-01]: checked-in callsite を棚卸しした結果、production 側で `py_at(object)` / `py_slice(object)` を使っていたのは generated `std/json` の `JsonArr::get*` 群だけで、残りは `test_cpp_runtime_iterable.py` の inventory guard だった。`py_runtime.h` から helper を落とす前に `JsonArr.raw: object` から typed `list<object>` read helper `_json_array_items` を経由する順序を固定した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-01]: `src/pytra/std/json.py` に `@abi(ret="value")` 付き `_json_array_items` / `_json_new_array` を導入し、`JsonArr.get*` は `_json_array_items(self.raw)[index]` へ、`_parse_array()` は typed `list<object>` local を `_json_new_array()` から初期化して `append` する形へ寄せた。`stmt.py` では `@abi(ret="value")` の call return から plain local を宣言する際、`list[...]` を `list<...>` 署名で受けるよう型推論を補強した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-02]: representative regression は `test_py2cpp_features.py` の JSON runtime emit assertion を更新し、`py_at(this->raw, ...)` が消え、`list<object> _json_array_items(const object& raw)` と `py_at(_json_array_items(this->raw), ...)` が生成されることを固定した。`test_cpp_runtime_iterable.py` では object read bridge signature の `NotIn` guard を維持した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-02]: verification は `test_py2cpp_features.py -k json`, `test_cpp_runtime_iterable.py`, `test_pylib_json.py`, fixture parity `cases=3 pass=3 fail=0`, sample parity `cases=18 pass=18 fail=0` を通した。`py_runtime.h` から `py_at(const object&, int64)` と 2 つの `py_slice(const object&, ...)` は削除済みで、read fallback は generated JSON helper 側へ閉じ込めた。
