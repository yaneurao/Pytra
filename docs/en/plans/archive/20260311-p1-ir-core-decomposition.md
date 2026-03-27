<a href="../../../ja/plans/archive/20260311-p1-ir-core-decomposition.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

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
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S3-01] Continue moving remaining `core.py` clusters into dedicated modules in bundle-sized slices.
- [x] [ID: P1-IR-CORE-DECOMPOSITION-01-S4-01] Run representative IR/selfhost regressions and stabilize the split with compressed progress notes.

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
- 2026-03-11: Added `core_stmt_analysis.py`, then moved `_sh_extract_leading_docstring`, `_sh_collect_yield_value_types`, `_sh_collect_return_value_types`, `_sh_infer_return_type_for_untyped_def`, `_sh_collect_store_name_ids`, `_sh_collect_reassigned_names`, `_sh_build_arg_usage_map`, and `_sh_make_generator_return_type` out of `core.py`. The statement-analysis cluster now lives behind a dedicated source-contract test.
- 2026-03-11: Added `core_type_semantics.py`, then moved `_sh_default_type_aliases`, `_sh_is_type_expr_text`, `_sh_typing_alias_to_type_name`, `_sh_register_type_alias`, `_sh_ann_to_type`, `_sh_ann_to_type_expr`, `_sh_type_expr_to_type_name`, and `_sh_split_args_with_offsets` out of `core.py`. `_sh_set_parse_context` stays in `core.py` because it mutates the `_SH_*` parse context, and the type-helper cluster is locked by a dedicated source-contract test.
- 2026-03-11: Added `core_import_semantics.py`, then moved `_sh_append_import_binding`, `_sh_import_binding_fields`, `_sh_make_import_resolution_binding`, `_sh_is_host_only_alias`, `_sh_register_import_symbol`, and `_sh_register_import_module` out of `core.py`. The registration helpers now take import stores and builder callbacks explicitly, and the import-binding cluster is locked by a dedicated source-contract test.
- 2026-03-11: Added `core_import_module_builders.py`, then moved `_sh_make_import_alias`, `_sh_make_import_binding`, `_sh_make_import_symbol_binding`, `_sh_make_qualified_symbol_ref`, `_sh_make_import_stmt`, `_sh_make_import_from_stmt`, `_sh_make_module_source_span`, `_sh_make_import_resolution_meta`, `_sh_make_module_meta`, and `_sh_make_module_root` out of `core.py`. Representative `Import` / `ImportFrom` / module-root call sites now route through the split module, and the builder cluster is locked by a dedicated source-contract test.
- 2026-03-11: Added `core_signature_semantics.py`, then moved `_sh_parse_typed_binding`, `_sh_parse_augassign`, and `_sh_parse_def_sig` out of `core.py`. `_sh_parse_def_sig` now takes `_SH_TYPE_ALIASES`, `_make_east_build_error`, `_sh_span`, and `_sh_make_def_sig_info` via callback injection, and the signature cluster is locked by a dedicated source-contract test.
- 2026-03-11: Added `core_builder_base.py`, `core_ast_builders.py`, and `core_stmt_builders.py`, then moved the node/value/trivia primitives, expression builders, and statement builders out of `core.py`. `test_east_core_source_contract_builders.py` and `test_east_core_source_contract_stmt_builders.py` now track helper-definition ownership plus representative call sites against the split-module layout.
- 2026-03-11: Added `core_expr_precedence.py` and moved the `lambda/ifexp/or..unary` precedence parser cluster out of `core.py`. `_ShExprParser` now keeps only `_raise_expr_build_error` for that lane, and source-contract coverage tracks the split module directly.
- 2026-03-11: Added `core_entrypoints.py`, then moved `EastBuildError`, `_make_east_build_error`, `convert_source_to_east*`, and `convert_path` out of `core.py`. `core.py` now keeps only the self-hosted parser implementation and re-exports the public entrypoints, while `east_io.py` and `compiler/east_parts` now follow the split module.
- 2026-03-11: Expanded `core_parse_context.py` into the source of truth for parse/import/runtime/template context so `_SH_IMPORT_SYMBOLS`, `_SH_IMPORT_MODULES`, `_SH_EMPTY_SPAN`, and the runtime ABI/template mode constants moved out of `core.py` as well. Source-contract coverage now tracks this through a dedicated parse-context test.
- 2026-03-11: Added `core_parse_context.py` and moved `_SH_FN_RETURNS`, `_SH_CLASS_METHOD_RETURNS`, `_SH_CLASS_BASE`, `_SH_TYPE_ALIASES`, and `_sh_set_parse_context` out of `core.py`. `core.py` now imports the shared parse-context state, while type/signature helper call sites keep using the same `_SH_TYPE_ALIASES` handle.
- 2026-03-11: Added `core_expr_parser_base.py`, then moved `_tokenize`, `_cur`, `_eat`, `_node_span`, `_src_slice`, and `parse` out of `core.py`. The tokenizer now depends directly on `core_string_semantics.py`, and source-contract coverage moved into a dedicated parser-base test file.
- 2026-03-11: Moved `_sh_extract_adjacent_string_parts` into `core_string_semantics.py`, then added `core_stmt_if_semantics.py` to split the `if/elif/else tail` cluster out of `core.py`. Dedicated source-contract coverage now locks both the split location and the callback wiring.
- 2026-03-11: Moved the `_ShExprParser` resolution helper cluster (callable return, method return, named-call return, attr metadata, union splitting, and dynamic guards) into `core_expr_resolution_semantics.py`, separating the call/attr type-resolution lane into a dedicated mixin.
- 2026-03-11: Moved the `call annotation` cluster (named/attr/callee call annotation, runtime/builtin dispatch, and call payload construction) into `core_expr_call_annotation.py`, leaving `core.py` with call/attr/subscript suffix orchestration and mixin wiring only.
- 2026-03-11: Moved the generator-arg / comprehension-target parser cluster into `core_expr_call_args.py`, removing `_parse_comp_target` / `_parse_call_arg_expr` from `core.py`. Source-contract coverage now uses the `def _make_bin` boundary in the call-dispatch / expr-suffix tests.
- 2026-03-11: Added `core_expr_primary.py`, then moved the `_make_bin` / `_parse_primary` cluster out of `core.py`. `core.py` now keeps only thin wrappers for that lane, and a dedicated primary source-contract test locks the split-module layout.
- 2026-03-11: Promoted `_parse_primary` in `core_expr_primary.py` to a mixin and removed the primary wrapper from `core.py`. The postfix source-contract boundary is now normalized on `def _make_bin`, so the primary split no longer depends on a wrapper import path.
- 2026-03-11: Added `core_expr_lowered.py`, moved the `_sh_parse_expr_lowered` cluster out of `core.py`, left only a thin wrapper in `core.py`, and updated the expr-suffix source-contract to treat the split module as the source of truth.
- 2026-03-11: `S3-01` is complete. `core.py` is now down to 214 lines and keeps only the three thin wrappers `_sh_parse_stmt_block_mutable`, `_sh_parse_stmt_block`, and `convert_source_to_east_self_hosted`.
- 2026-03-11: Start `S4-01` by adding `test_east_core_source_contract_core_surface.py` so the thin-facade contract and representative IR/selfhost regressions stay locked.
- 2026-03-11: Moved `_ShExprParser` / `_sh_parse_expr` / `_sh_parse_expr_lowered` into `core_expr_shell.py` and split the `expr_suffix` / `call_dispatch` / `call_metadata` / `runtime_builtins` source-contracts between the `core.py` facade and the parser shell.
- 2026-03-11: Ran `test_east_core_source_contract_core_surface.py`, the full `test_east_core*.py` suite, `test_prepare_selfhost_source.py`, and `build_selfhost.py`, then fixed the thin-facade end state at `core.py=214 lines` / `test_east_core.py=44 lines` with representative regressions. `S4-01` is complete and this plan moves to archive.
