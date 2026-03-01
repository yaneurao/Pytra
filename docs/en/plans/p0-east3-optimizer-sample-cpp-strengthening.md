# P0: Strengthen EAST3 optimization layer (improve sample C++ output)

Last updated: 2026-02-27

Related TODO:
- `ID: P0-EAST3-OPT-SAMPLE-CPP-01` in `docs/ja/todo/index.md`

Background:
- Output in `sample/cpp` still contains redundant patterns that can be absorbed at the EAST3 stage (`object`-relay iteration, redundant `py_to<T>`, generic `range` conditions, `make_object(py_repeat(...))`, etc.).
- Current optimizer v1 is fail-closed and narrow in scope, so noise that directly affects readability and runtime cost is not sufficiently reduced, including in `sample/18`.
- Handling each case only in the C++ emitter bloats backend-specific logic, so shareable parts should move into the EAST3 optimization layer.

Goal:
- Preprocess conspicuous redundant conversions in key `sample/cpp` cases at the EAST3 stage and improve readability and efficiency of C++ emitter output.

Scope:
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py`
- `src/pytra/compiler/east_parts/east3_optimizer.py` (pass registration/order)
- EAST3 optimizer unit tests and CLI tests
- Minimum necessary regeneration checks for `sample/cpp`

Out of scope:
- C++ emitter-specific final formatting (paren formatting, naming style changes)
- Aggressive optimizations with semantic changes
- Backend-specific code-style improvements for non-C++ targets

Acceptance criteria:
- For each of the 7 subtasks, a corresponding pass (or extension of an existing pass) is implemented and managed by the optimizer in a disable-able form.
- On regenerating `sample/05,06,07,09,13,14,16,18`, at least part of target patterns is collapsed.
- Switching `--east3-opt-level 0/1/2` does not produce semantic differences (no regressions by existing parity procedure).

Verification commands:
- `python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_east3_optimizer_cli.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-27: Based on review of actual `sample/cpp` output, filed 7 P0 items to absorb first in EAST3 optimization layer: range normalization extension, typed enumerate, cast-chain collapse, loop-invariant hoist extension, typed repeat, dict key cast reduction, and direct tuple-unpack expansion.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-01] Extended `RangeForCanonicalizationPass` so for `range(...)` with constant `step` and `int/int64` args, dynamic `stop` is normalized into `StaticRangeForPlan`. Added `test_range_for_canonicalization_pass_accepts_dynamic_stop_with_const_step` / `...skips_dynamic_stop_when_type_is_unknown` to lock regressions.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-02] Added `TypedEnumerateNormalizationPass` to supplement `iter_item_type=tuple[int64,T]` and `target_plan` type annotations for `ForCore(RuntimeIterForPlan)` with `py_enumerate(list[T])`. Strengthened C++ emitter to choose typed loop headers even with `iter_item_type/iter_element_type` hints, and locked regressions with `test_typed_enumerate_normalization_pass_*` / `test_emit_stmt_forcore_runtime_tuple_target_uses_iter_item_hint_when_resolved_type_unknown`.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-03] Added `NumericCastChainReductionPass` to fail-closed collapse chains of identity numeric casts (`static_cast` / `Unbox`). Added pass name to `opt_pass_spec` disable path and locked no-op/skip conditions (including `object/Any`) with `test_numeric_cast_chain_reduction_pass_*`.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-04] Added `LoopInvariantCastHoistPass` to hoist numeric promotion casts in `BinOp` inside `ForCore(StaticRangeForPlan)` (especially RHS `int -> float64`) to preheaders. Verified in `sample/06_julia_parameter_sweep.py` that `float64` conversions for `height-1` / `width-1` / `frames_n` moved outside loops, and added `test_loop_invariant_cast_hoist_pass_*` for regression lock.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-05] Added `TypedRepeatMaterializationPass` implementing list-repeat inference for `BinOp(Mult)` (`list[T] * int -> list[T]`) and `ListComp` output-type completion (`list[unknown] -> list[list[T]]`). Confirmed `make_object(py_repeat(...))` occurrences drop to 0 across full `sample/py` regeneration, and added `test_typed_repeat_materialization_pass_*` for regression lock.
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-06] Added `DictStrKeyNormalizationPass` to mark key nodes for `dict[str, V]` with `dict_key_verified` (and supplement `resolved_type=str` when needed). Updated C++ emitter to omit `py_to_string` on keys with this flag, and verified direct keying in `sample/18` for `env[node->name]` / `env[stmt->name]`. Added `test_dict_str_key_normalization_pass_*` / `test_coerce_dict_key_expr_skips_str_cast_when_key_is_verified`, and passed `check_py2cpp_transpile.py` (`checked=133 ok=133 fail=0 skipped=6`).
- 2026-02-28: [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-07] Added `TupleTargetDirectExpansionPass` to attach `direct_unpack` metadata to flat `TupleTarget`. Added emitter path to use structured-binding headers (`for (const auto& [a, b] : iter)`) for typed iterables with this metadata, collapsing `sample/18` `enumerate` loops without `py_at/py_to` chains. Locked regressions with `test_tuple_target_direct_expansion_pass_*` / `test_emit_stmt_forcore_runtime_tuple_target_direct_unpack_uses_structured_binding`.

## Breakdown

- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-01] Implement `RangeForCanonicalizationPass` extension (`stop` dynamic + `step` constant) and suppress generation of `for (...; N>0 ? ... : ...)` form.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-02] Implement typed iteration normalization for `enumerate(list[T])` and collapse `object + py_at + py_to` chains.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-03] Add numeric cast-chain collapse pass and reduce chains of typed `py_to<T>`.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-04] Implement hoisting for loop-invariant type conversions/denominators and lighten inner-loop work.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-05] Implement typed materialization normalization for type-known `py_repeat` initialization.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-06] Implement removal of unnecessary `to_string` in `dict<str, V>` key paths.
- [x] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-07] Implement elimination of tuple-unpack temporaries (direct `TupleTarget` expansion).
