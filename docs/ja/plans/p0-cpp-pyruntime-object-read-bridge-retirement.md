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

- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01] `py_runtime.h` の object read bridge を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-01] `py_at(object)` / `py_slice(object)` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-02] `JsonArr` 依存と削除順序を決定ログへ固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-01] JSON / runtime callsite を typed / nominal accessor へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-02] representative regression を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-01] `py_at(object)` / `py_slice(object)` を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-08: 本計画は object collection bridge 第2波として read lane だけを扱い、mutation lane の再導入は認めない。
