<a href="../../../en/plans/archive/20260312-p4-crossruntime-pyruntime-emitter-future-shrink.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S2-02] Rust / C# emitter の shared thin helper と C# bytearray compat seam を棚卸しし、future reduction order を固定した。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S3-01] representative smoke / source guard / inventory drift guard を future-shrink baseline に合わせて更新した。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-FUTURE-SHRINK-01-S4-01] future emitter shrink の handoff 条件を次段 task に接続した。

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

## Future Representative Guard Baseline

- `cpp_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/cpp/test_east3_cpp_bridge.py`
  - representative tests:
    - `test_render_expr_supports_east3_obj_boundary_nodes`
    - `test_transpile_representative_nominal_adt_match_emits_if_else_chain`
  - source guard paths:
    - `src/backends/cpp/emitter/cpp_emitter.py`
    - `src/backends/cpp/emitter/runtime_expr.py`
    - `src/backends/cpp/emitter/stmt.py`
- `rs_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/rs/test_py2rs_smoke.py`
  - representative tests:
    - `test_type_predicate_nodes_are_lowered_without_legacy_bridge`
  - source guard path:
    - `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - smoke: `test/unit/backends/cs/test_py2cs_smoke.py`
  - representative tests:
    - `test_type_predicate_nodes_are_lowered_without_legacy_bridge`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - smoke: `test/unit/backends/cs/test_py2cs_smoke.py`
  - representative tests:
    - `test_bytearray_mutation_stays_on_runtime_helpers_but_list_append_does_not`
    - `test_bytearray_index_and_slice_compat_helpers_stay_explicit`
  - source guard path:
    - `src/backends/cs/emitter/cs_emitter.py`
- inventory drift guard:
  - future representative subset は `check_crossruntime_pyruntime_emitter_inventory.py` の `FUTURE_REPRESENTATIVE_LANE_MANIFEST` と `FUTURE_SOURCE_GUARD_PATHS` で固定する。

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

## Rust / C# Shared Type ID Classification

- `future_reducible`
  - none
- `must_remain_until_runtime_task`
  - Rust:
    - `py_runtime_value_type_id`
    - `py_runtime_value_isinstance`
    - `py_runtime_type_id_is_subtype`
    - `py_runtime_type_id_issubclass`
  - C#:
    - `py_runtime_value_type_id`
    - `py_runtime_value_isinstance`
    - `py_runtime_type_id_is_subtype`
    - `py_runtime_type_id_issubclass`
  - 解釈:
    - どちらも shared thin helper 自体が runtime contract なので、backend local へ押し戻す前に runtime / type-id ownership task が必要になる。

## C# Bytearray Compatibility Classification

- `future_reducible`
  - `py_append` in `src/backends/cs/emitter/cs_emitter.py`
  - `py_pop` in `src/backends/cs/emitter/cs_emitter.py`
  - 解釈:
    - これは `bytearray` compat に閉じた emitter-side seam で、shared type-id contract と違って backend local helper へ押し戻せる。
- `must_remain_until_runtime_task`
  - none

## Handoff Condition

- C++ emitter が thin helper 以外の generic / object-type-id alias を再流入させないこと。
- Rust / C# emitter が shared thin helper を増やさないこと。
- C# `bytearray` compat seam が list / bytes mutation へ再拡大しないこと。
- これらが inventory tool で固定されたら、次段の header shrink / runtime externalization task へ handoff する。

## Handoff Targets

- `cpp_header_shrink`
  - target plan:
    - `docs/ja/plans/archive/20260312-p0-cpp-pyruntime-final-shrink.md`
  - trigger bucket:
    - `cpp_emitter_shared_type_id_residual`
  - handoff condition:
    - `future_reducible` subset が `py_runtime_value_type_id` のみのままで、representative/source guard drift が空であること。
- `runtime_sot_followup`
  - target plan:
    - `docs/ja/plans/p2-runtime-sot-linked-program-integration.md`
  - trigger bucket:
    - `rs_emitter_shared_type_id_residual`
  - handoff condition:
    - shared `type_id` seam が `must_remain_until_runtime_task` のみで固定され、runtime/type-id ownership を runtime SoT 側へ送る条件が明確であること。
- `cs_bytearray_localization`
  - target plan:
    - `docs/ja/plans/archive/20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md`
  - trigger bucket:
    - `crossruntime_mutation_helper_residual`
  - handoff condition:
    - C# `bytearray` compat seam が `py_append` / `py_pop` に閉じていて、list / bytes mutation へ再拡大していないこと。

## 決定ログ

- 2026-03-12: archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` / `...-RESIDUAL-REDUCTION-01` は current residual の整理までは完了しているため、この follow-up は「その後の future reduction」だけに責務を限定する。
- 2026-03-12: `S1-01` では current residual inventory を baseline として固定し、future reduction order を `C++ shared type_id -> Rust shared type_id -> C# shared type_id -> C# bytearray compat` に置いた。
- 2026-03-12: `S2-01` では C++ shared type-id residual を `future_reducible=py_runtime_value_type_id only` と `must_remain_until_runtime_task=nominal ADT match / type-predicate seam` に分け、inventory tool でも同じ分類を guard するようにした。
- 2026-03-12: `S2-02` では Rust/C# shared thin seam はすべて `must_remain_until_runtime_task`、C# `bytearray` compat seam (`py_append` / `py_pop`) は `future_reducible` に固定し、future reduction order の根拠を inventory tool に持たせた。
- 2026-03-12: `S3-01` では future-shrink follow-up が実際に依存する representative smoke / source guard subset を `FUTURE_REPRESENTATIVE_LANE_MANIFEST` と `FUTURE_SOURCE_GUARD_PATHS` で固定し、classification だけでなく drift guard も future baseline 単位で監視するようにした。
- 2026-03-12: `S4-01` では handoff 先を `cpp_header_shrink` / `runtime_sot_followup` / `cs_bytearray_localization` の 3 target に固定し、plan path と trigger bucket と handoff 条件を inventory tool 側でも source-of-truth として監視するようにした。
