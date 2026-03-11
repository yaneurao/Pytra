# P4 Crossruntime PyRuntime Emitter Future Shrink

最終更新: 2026-03-12

目的:
- `py_runtime.h` のさらなる縮小や thin seam 抽出に先立ち、C++ / Rust / C# emitter 側に意図的に残している residual seam を次段でどう減らすかを整理する。
- archived 済み `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` / `...-RESIDUAL-REDUCTION-01` の完了状態を baseline とし、その後に残る emitter-side follow-up を low priority の backlog として可視化する。
- `shared type_id thin seam` と `C# bytearray compat seam` のどこが backend local へ押し戻せるかを bundle 単位で決め、次の header shrink / runtime SoT task への handoff 条件を固定する。

背景:
- 既存の emitter shrink 系 `P4` は archive 済みで、current residual inventory は [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py) に固定されている。
- 現在の emitter residual は「未分類の負債」ではなく intentional seam だが、`py_runtime.h` をさらに縮めるには C++ / Rust / C# emitter 側の follow-up がなお必要である。
- とくに C++ emitter の `py_runtime_value_*` / `py_runtime_type_id_is_*`、Rust/C# emitter の shared thin helper、C# `bytearray` mutation compat は、次段で local runtime trait / helper / backend-local lowering へ押し戻せる可能性がある。
- ただし直近で優先すべき blocker ではないため、parser / lowering / runtime 本流より低い `P4` に置く。

非対象:
- 今この task で `py_runtime.h` を直接縮め切ること。
- Rust / C# runtime builtins 全面刷新。
- 新しい object system や type_id model の設計変更。

受け入れ基準:
- current emitter residual baseline と follow-up bundle order が live TODO / plan / inventory tool に固定されている。
- C++ / Rust / C# emitter の残存 seam が `future_reducible` と `must_remain_until_runtime_task` の観点で整理されている。
- representative smoke / source guard / inventory drift guard が future shrink 前提の監視点を持つ。
- 次段の `py_runtime.h` shrink または runtime SoT task に handoff する条件が plan に書かれている。
- `docs/en/` mirror が日本語版と同じ内容に追従している。

## 子タスク

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S1-01] live plan / TODO / inventory tool に future-shrink follow-up の baseline と bundle order を固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S2-01] C++ emitter の shared type_id thin seam を棚卸しし、backend-local へ押し戻せる caller と must-remain seam を分類する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S2-02] Rust / C# emitter の shared thin helper と C# bytearray compat seam を棚卸しし、future reduction order を固定する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S3-01] representative smoke / source guard / inventory drift guard を future-shrink baseline に合わせて更新する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S4-01] future emitter shrink の handoff 条件を次段 task に接続する。

## Current Baseline

- `cpp_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - source guard paths:
    - `src/backends/cpp/emitter/cpp_emitter.py`
    - `src/backends/cpp/emitter/runtime_expr.py`
    - `src/backends/cpp/emitter/stmt.py`
- `rs_emitter_shared_type_id_residual`
  - same 4 helper names
  - source guard path:
    - `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - same 4 helper names
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - `py_append`
  - `py_pop`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
  - current interpretation:
    - `bytearray` compat seam only

## Future Reduction Order

1. `cpp_emitter_shared_type_id_residual`
2. `rs_emitter_shared_type_id_residual`
3. `cs_emitter_shared_type_id_residual`
4. `crossruntime_mutation_helper_residual`

## C++ Shared Type ID Classification

- `future_reducible`
  - `py_runtime_value_type_id` in `src/backends/cpp/emitter/cpp_emitter.py`
  - 解釈:
    - value type-id 参照は emitter local metadata / lowered helper へ押し戻せる余地があり、nominal ADT match や type-predicate の shared contract からは独立している。
- `must_remain_until_runtime_task`
  - `py_runtime_value_isinstance` in `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_value_isinstance` in `src/backends/cpp/emitter/stmt.py`
  - `py_runtime_type_id_is_subtype` in `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_type_id_issubclass` in `src/backends/cpp/emitter/runtime_expr.py`
  - 解釈:
    - representative nominal ADT match と type-predicate lowering の shared thin seam なので、runtime / type-id ownership task が先に動くまでは intentional residual として保持する。

## Handoff Condition

- C++ emitter が thin helper 以外の generic / object-type-id alias を再流入させないこと。
- Rust / C# emitter が shared thin helper を増やさないこと。
- C# `bytearray` compat seam が list / bytes mutation へ再拡大しないこと。
- これらが inventory tool で固定されたら、次段の header shrink / runtime externalization task へ handoff する。

## 決定ログ

- 2026-03-12: archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` / `...-RESIDUAL-REDUCTION-01` は current residual の整理までは完了しているため、この follow-up は「その後の future reduction」だけに責務を限定する。
- 2026-03-12: `S1-01` では current residual inventory を baseline として固定し、future reduction order を `C++ shared type_id -> Rust shared type_id -> C# shared type_id -> C# bytearray compat` に置いた。
- 2026-03-12: `S2-01` では C++ shared type-id residual を `future_reducible=py_runtime_value_type_id only` と `must_remain_until_runtime_task=nominal ADT match / type-predicate seam` に分け、inventory tool でも同じ分類を guard するようにした。
