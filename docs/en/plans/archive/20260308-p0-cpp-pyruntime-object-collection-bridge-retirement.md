<a href="../../ja/plans/archive/20260308-p0-cpp-pyruntime-object-collection-bridge-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-collection-bridge-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260308-p0-cpp-pyruntime-object-collection-bridge-retirement.md`

# P0: C++ `py_runtime.h` object collection bridge 第1波退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)
- [20260308-p0-cpp-pyruntime-object-lane-retirement.md](./archive/20260308-p0-cpp-pyruntime-object-lane-retirement.md)

背景:
- `P0-CPP-PYRUNTIME-OBJECT-LANE-01` で `py_runtime.h` から object/optional dict access convenience と object arithmetic を削除した。
- その後、本計画の first wave として mutation / lookup 側の `object` collection bridge を削除し、`src/runtime/cpp/native/core/py_runtime.h` に残る collection bridge は read helper (`py_at(const object&, int64)`, `py_slice(const object&, ...)`) だけになった。
- 今回削除した helper 群は次のとおり。
  - `py_append(const object&, ...)`
  - `py_set_at(const object&, ...)`
  - `py_extend(const object&, ...)`
  - `py_pop(const object&, ...)`
  - `py_clear(const object&)`
  - `py_reverse(const object&)`
  - `py_sort(const object&)`
  - `py_index(const object&, ...)`
- 現在の decode-first / typed value path 方針では、`object` のまま collection helper を呼ぶのは permanent API ではない。JSON や dynamic data は `JsonValue` / `JsonObj` / `JsonArr` または明示 decode を経て typed helper へ渡すべきである。

目的:
- `py_runtime.h` から mutation / lookup の `object` collection bridge を縮退し、typed list / dict / string path を正本にする。
- `object` を list/dict 代替として使える前提を runtime surface から外し、decode-first 契約と整合させる。
- `py_runtime.h` の責務を low-level bridge と typed helper glue へさらに寄せる。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の次の `object` collection bridge first wave
  - `py_append(const object&, const object&)`
  - `py_set_at(const object&, int64, const object&)`
  - `py_extend(const object&, const object&)`
  - `py_pop(const object&)`
  - `py_pop(const object&, int64)`
  - `py_clear(const object&)`
  - `py_reverse(const object&)`
  - `py_sort(const object&)`
  - `py_index(const object&, const object&)`
- これに伴う representative runtime tests / parity / docs

非対象:
- `py_at(const object&, int64)` と `py_slice(const object&, ...)` の read bridge（`JsonArr.raw: object` 依存が残るため別 tranche）
- `begin/end(const object&)` や `py_iter_or_raise(const object&)` などの dynamic iteration bridge
- `PyObj` / `object` / `make_object` / `py_to_*` 本体
- `JsonValue` nominal carrier の full rollout
- header 分割

受け入れ基準:
- 上記 first-wave の `object` collection bridge が `py_runtime.h` から削除される。
- checked-in sample / runtime / codegen で必要な経路は typed list / dict / string helper へ寄る。
- `py_at(object)` / `py_slice(object, ...)` は本計画では保留扱いに固定され、次 tranche へ送られる。
- representative C++ runtime tests と fixture/sample parity が維持される。
- `py_runtime.h` の行数削減が確認できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_boxing.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root sample --all-samples`

## 1. 基本方針

1. `object` のまま collection helper を呼ぶ lane は runtime convenience で救済しない。
2. list/dict/string の typed helper と `JsonValue` decode-first を正本にする。
3. 削除前に checked-in callsite を棚卸しし、必要なら emitter / generated runtime 側を typed lane に寄せる。
4. `begin/end(object)` や `py_iter_or_raise(object)` のような dynamic iteration bridge は別 tranche に分離し、今回の P0 では触らない。

## 2. フェーズ

### Phase 1: 棚卸しと削除順序の固定

- checked-in の generated C++, sample/cpp, tests, emitter expectation を走査し、`object` collection bridge の実依存を棚卸しする。
- `py_at/py_slice` の read path、mutation path、`py_index` の 3 群に分ける。
- 削除順序と「残さない compat lane」を決定ログへ固定する。

### Phase 2: mutation / lookup bridge の撤去

- `py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort` の `object` lane を削除する。
- `py_index(const object&, const object&)` も削除し、typed list lane へ統一する。
- inventory guard を更新し、object collection bridge が戻らないことを固定する。

### Phase 3: read bridge の保留固定

- `py_at(const object&, int64)` と `py_slice(const object&, ...)` は `JsonArr.raw: object` 依存が解けるまで削除しない。
- 本 tranche では read bridge 保留の理由と次の依存解消条件だけを記録し、削除自体は次段へ送る。

### Phase 4: representative verification と close

- representative unit / fixture / sample parity を回す。
- `py_runtime.h` の行数差分を記録する。
- docs / archive / TODO 履歴を同期して閉じる。

## 3. 着手時の注意

- `src/runtime/cpp/generated/std/json.cpp` と `json.h` に未コミット差分が残っている可能性がある。今回の P0 では巻き込まない。
- `begin/end(const object&)` と `py_iter_or_raise(const object&)` は今回の非対象であり、誤って一緒に削らない。
- `sample/cpp/*.cpp` は generated artifact なので、source-of-truth は emitter / runtime / `sample/py` 側で直す。
- compile error 方針を frontend に既に入れていても、runtime inventory guard を残して再侵入を防ぐ。

## 4. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01] `py_runtime.h` の mutation / lookup `object` collection bridge を撤去し、typed list/dict/string path を正本に寄せる。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S1-01] `py_at/py_slice/py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort/py_index` の checked-in callsite と compat 依存を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S1-02] 削除順序と「残さない compat lane」を決定ログへ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S2-01] `py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort` の `object` lane を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S2-02] `py_index(const object&, const object&)` を削除し、inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S3-01] `py_at(const object&, int64)` と `py_slice(const object&, ...)` を保留扱いへ固定し、read bridge 依存を次段へ送る。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S3-02] read bridge 保留後の representative regression / inventory 注記を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S4-01] representative unit / fixture / sample parity と行数差分を確認する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-COLLECTION-01-S4-02] docs / archive / TODO 履歴を同期して本計画を閉じる。

## 5. 決定ログ

- 2026-03-08: 本計画では `begin/end(const object&)` や `py_iter_or_raise(const object&)` の dynamic iteration bridge は触らず、collection helper に限定して object lane を退役させる。
- 2026-03-08: checked-in sample/cpp と runtime test の大半は typed list/string lane を使っており、`object` collection bridge の直接依存は `test_cpp_runtime_iterable.py` の object mutation smoke にほぼ限られる。
- 2026-03-08: `src/runtime/cpp/generated/std/json.cpp` の `JsonArr::get*()` は現在 `JsonArr.raw: object` と `py_at(this->raw, ...)` / `py_len(this->raw)` に依存している。`py_at(object)` / `py_slice(object, ...)` の read bridge は、JSON runtime lane を typed/nominal carrier へ寄せる tranche まで本計画では削除しない。
- 2026-03-08: 第1削除順は mutation bridge (`py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort`) と `py_index(const object&, const object&)` に固定し、inventory guard で再侵入を防ぐ。read bridge (`py_at(object)`, `py_slice(object, ...)`) は本計画の TODO から外さず残すが、close 時点では保留扱いを明記して次 tranche へ送る。
- 2026-03-08: object mutation smoke は bridge API ではなく `obj_to_list_obj(...)->value` と `py_list_*_mut` の low-level lane に寄せて維持した。iterator が mutation 後の要素を観測する regression 自体は残す。
- 2026-03-08: representative verification は `test_cpp_runtime_iterable.py`, `test_cpp_runtime_boxing.py`, `check_runtime_std_sot_guard.py`, fixture parity `cases=3 pass=3 fail=0` を通した。sample parity は full run の `17/18` green に加えて、failure だった `18_mini_language_interpreter` を `cases=1 pass=1 fail=0` で再確認した。
- 2026-03-08: `py_runtime.h` の行数は本計画起票時比で `2337 -> 2246` に縮退した。read bridge (`py_at(object)`, `py_slice(object, ...)`) は current `JsonArr.raw: object` 依存が解けるまで次 tranche に送る。
