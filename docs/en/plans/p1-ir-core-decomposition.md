# P1: Decompose `core.py` and `test_east_core.py` in cluster-sized slices

Last updated: 2026-03-11

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-IR-CORE-DECOMPOSITION-01`

Background:
- `src/toolchain/ir/core.py` is 10,081 lines and `test/unit/ir/test_east_core.py` is 3,912 lines, making review and navigation expensive.
- `P2-COMPILER-TYPED-BOUNDARY-01-S3-02` did make progress on helper extraction, but the work regressed into one-helper-per-commit micro-slices.
- `test_east_core.py` mixes source-contract guards and parser behavior tests, so the next split boundary is no longer obvious.

Goal:
- Decompose `core.py` and `test_east_core.py` into responsibility-focused modules and test files that can be advanced in cluster-sized slices.
- Separate source-contract guards, parser behavior, and suffix/call clusters into clearer ownership boundaries.
- Compress TODO / plan progress notes back to cluster-sized summaries.

In scope:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_expr_*.py`
- `test/unit/ir/test_east_core.py`
- `test/unit/ir/test_east_core*.py`
- `docs/ja/todo/index.md`, `docs/en/todo/index.md`
- `docs/ja/plans/*.md`, `docs/en/plans/*.md`

Out of scope:
- IR spec changes
- New typed-boundary or nominal-ADT features
- Backend-specific codegen quality work

Acceptance criteria:
- `core.py` becomes easier to read by separating responsibilities such as builder/core, suffix parser, and call annotation clusters.
- `test_east_core.py` is split so source-contract guards and parser behavior are no longer interleaved.
- Each slice handles roughly 5-10 helpers or test clusters instead of returning to micro-commits.
- TODO / plan progress notes are compressed to cluster-level summaries.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-01] Inventory split boundaries in `core.py` and `test_east_core.py`, then lock the split order for source-contract, parser-behavior, and suffix/call clusters.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S1-02] Record the cluster-level progress-note rule in this plan and align TODO wording with it.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-01] Extract the leading source-contract builder cluster from `test_east_core.py` into a shared support module plus a dedicated test file.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-02] Split the remaining source-contract guards into cluster-specific `test_east_core_source_contract_*.py` files.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S2-03] Split parser behavior, diagnostics, and representative nominal-ADT tests into dedicated test files.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Continue moving remaining `core.py` clusters into dedicated modules in bundle-sized slices.
- [ ] [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] Run representative IR/selfhost regressions and stabilize the split with compressed progress notes.

Decision log:
- 2026-03-11: Created this task using `core.py=10081 lines` and `test_east_core.py=3912 lines` as the baseline. The first slice will extract the leading source-contract builder cluster from `test_east_core.py` into a shared support module and a dedicated test file.
- 2026-03-11: Future splits should operate on bundles of roughly 5-10 helpers or test clusters, not one-helper-per-commit micro-slices. TODO / plan notes should stay at the same bundle-level granularity.
- 2026-03-11: Keep only one-line cluster-level progress notes in TODO, and record verification logs or rationale in this plan's decision log. All later `S2+` slices should keep that convention.
- 2026-03-11: Added `test/unit/ir/_east_core_test_support.py` plus `test/unit/ir/test_east_core_source_contract_builders.py`, then moved the leading 10 builder source-contract guards out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_source_contract_expr_suffix.py`, then moved 10 call/attr/subscript source-contract guards out of `test_east_core.py`. `S2-02` stays open because more source-contract clusters remain.
- 2026-03-11: Added `test/unit/ir/test_east_core_source_contract_call_metadata.py`, then moved 10 method/named-call metadata source-contract guards out of `test_east_core.py`. `S2-02` remains open because call-suffix, parser-helper, and tuple-destructure clusters are still in the main file.
- 2026-03-11: Added `test/unit/ir/test_east_core_source_contract_runtime_builtins.py` plus `test/unit/ir/test_east_core_source_contract_call_dispatch.py`, then moved the remaining 19 runtime-builtin / named-call / call-suffix source-contract guards out of `test_east_core.py`. The tuple-destructure and residual-inline-kind guards were folded into existing source-contract files, so `test_east_core.py` now focuses on parser behavior and representative regressions.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_decorators.py`, then moved 10 representative extern / abi / template parser-behavior tests out of `test_east_core.py` to start `S2-03`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_types.py`, then moved 10 representative decode-first, type-expression, and `typing` / `__future__` parser-behavior tests out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_diagnostics.py`, then moved 3 object-receiver diagnostics out of `test_east_core.py`. The 7 decorator / abi / template negative cases were also moved into `test_east_core_parser_behavior_decorators.py`, removing the duplicate leading test and stray assertions from `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_exprs.py`, then moved 10 representative comprehension / lambda / fstring / yield / basic parser-acceptance tests out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_classes.py`, then moved 7 representative class-storage / dataclass / nominal-ADT / enum parser-behavior tests out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_runtime.py`, then moved 12 representative runtime-annotation / builtin-call / pathlib / json / iter-lowering parser-behavior tests out of `test_east_core.py`.
- 2026-03-11: Added `test/unit/ir/test_east_core_parser_behavior_statements.py`, then moved 6 representative identifier/import ambiguity, `super()`, bare `return`, arg-usage, and trailing-semicolon parser-behavior tests out of `test_east_core.py`. Only 3 residual source-contract regressions remain in the main file.
- 2026-03-11: `S2-03` is complete now that `test_east_core.py` contains only the 3 residual source-contract regressions. The next bundle is `S3-01`, which will move the declaration / class-semantics cluster out of `core.py` into dedicated modules.
- 2026-03-11: Added `core_class_semantics.py`, then moved `_sh_make_decl_meta`, `_sh_make_nominal_adt_v1_meta`, the dataclass value-safe checks, and nominal-ADT class metadata collection out of `core.py`. The remaining `core.py` side keeps only the decorator parser and class-parse orchestration.
- 2026-03-11: Moved `_apply_attr_expr_annotation`, `_annotate_attr_expr`, and `_annotate_subscript_expr` into `core_expr_attr_subscript_annotation.py`, then updated `test_east_core_source_contract_expr_suffix.py` so the attr/subscript annotation cluster is read from the split module.
- 2026-03-11: Added `core_decorator_semantics.py`, then moved `_sh_parse_decorator_head_and_args`, `_sh_is_dataclass_decorator`, `_sh_is_sealed_decorator`, `_sh_is_abi_decorator`, and `_sh_is_template_decorator` out of `core.py`. The decorator cluster is now locked by a dedicated source-contract test file.
- 2026-03-11: Added `core_extern_semantics.py`, then moved `_sh_expr_attr_chain`, `_sh_is_extern_symbol_ref`, and `_sh_collect_extern_var_metadata` out of `core.py`. The ambient extern-binding cluster is now locked by a dedicated source-contract test file.
- 2026-03-11: Added `core_runtime_decl_semantics.py`, then moved `_sh_parse_runtime_abi_string_literal`, `_sh_parse_runtime_abi_mode`, and `_sh_parse_runtime_abi_args_map` out of `core.py`. The runtime ABI literal/mode cluster is now locked by a callback-injection source-contract test.
- 2026-03-11: Also moved `_sh_parse_runtime_abi_decorator`, `_sh_collect_runtime_abi_metadata`, `_sh_parse_template_decorator`, and `_sh_collect_template_metadata` into `core_runtime_decl_semantics.py`, leaving the function-parse site to call collectors only through callback injection.
- 2026-03-11: Added `_sh_collect_function_runtime_decl_metadata` plus class/method/top-level runtime ABI/template misuse guard helpers to `core_runtime_decl_semantics.py`, further shrinking `core.py` to declaration-parse orchestration.
- 2026-03-11: Added `core_string_semantics.py`, then moved `_sh_scan_string_token`, `_sh_decode_py_string_body`, and `_sh_append_fstring_literal` out of `core.py`. The f-string literal append helper now returns a thin `Constant` node dict without depending back on `core.py`.
- 2026-03-11: Added `core_text_semantics.py`, then moved `_sh_is_identifier`, `_sh_strip_utf8_bom`, `_sh_is_dotted_identifier`, `_sh_split_top_keyword`, `_sh_split_top_level_as`, `_sh_parse_import_alias`, and `_sh_parse_dataclass_decorator_options` out of `core.py`. Import-alias and dataclass-option parsing are now locked by callback-injection source-contract coverage.
- 2026-03-11: Added `core_string_semantics.py`, then moved `_sh_scan_string_token`, `_sh_decode_py_string_body`, and `_sh_append_fstring_literal` out of `core.py`. String token scanning now receives `_make_east_build_error` / `_sh_span` via callback injection and is locked together with f-string literal append by source-contract coverage.
- 2026-03-11: Added `core_stmt_text_semantics.py`, then moved `_sh_split_top_level_assign`, `_sh_strip_inline_comment`, `_sh_raise_if_trailing_stmt_terminator`, `_sh_split_top_level_from`, `_sh_split_top_level_in`, `_sh_split_top_level_colon`, `_sh_parse_except_clause`, `_sh_parse_class_header_base_list`, and `_sh_parse_class_header` out of `core.py`. The statement/header text helper cluster now receives `make_east_build_error`, `make_span`, and `split_top_commas` via callback injection and is locked by a dedicated source-contract test.
- 2026-03-11: Expanded `core_stmt_text_semantics.py` to cover logical-line merge, top-level split, comprehension-target binding, and indented-block collection, then removed the duplicate stmt-text helper definitions from `core.py`. Source-contract coverage now checks the stmt-text helper imports, representative call sites, and their absence from `core.py` in one place.
