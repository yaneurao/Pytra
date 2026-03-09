# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-10

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details (decisions and verification logs) must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file (keep the parent checkbox open until the parent `ID` is completed).
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` (or its child `ID`).
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` (or `/tmp` only when necessary), and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P2: Move compiler boundaries to typed carriers and retreat internal object-carrier / `make_object` usage

Context: [docs/ja/plans/p2-compiler-typed-boundary.md](../plans/p2-compiler-typed-boundary.md)

1. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01] Move compiler boundaries to typed carriers and retreat internal object-carrier / `make_object` usage.
2. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] Inventory remaining `dict[str, object]`, `list[object]`, `make_object`, and `py_to` usage across `transpile_cli`, `backend_registry_static`, selfhost parser paths, and generated compiler runtime, then classify each usage as `compiler_internal`, `json_adapter`, `extern_hook`, or `legacy_bridge`.
3. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] Lock the typed-boundary contract and non-goals so they stay consistent with `spec-dev`, `spec-runtime`, and `spec-boxing`.
4. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] Define typed carrier specs for compiler root payloads (EAST document, backend spec, layer options, emit request/result).
5. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Introduce typed carriers and thin legacy adapters in the Python source of truth.
6. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] Introduce typed carrier mirrors or typed wrapper APIs in the C++ selfhost/native compiler interfaces and reduce raw `dict<str, object>` exchange.
7. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Move selfhost parser / EAST builder node construction onto typed constructors / builder helpers and gradually retire direct `dict<str, object>{{...}}` assembly.
8. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Retreat remaining `make_object` usage in generated compiler / selfhost runtime down to serialization/export seams only.
9. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Separate JSON, extern/hooks, and other intentionally dynamic carriers from the compiler typed model behind `JsonValue` or explicit adapters.
10. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] Label every remaining `make_object` / `py_to` / `obj_to_*` usage and add guards that reject uncategorized reintroduction.
11. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] Refresh selfhost build/diff/prepare/bridge regressions and lock non-regression after the typed-boundary changes.
12. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] Update docs / TODO / archive and record whether each remaining `make_object` usage is `user boundary only` or `explicit adapter only`.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] Inventoried object-carrier usage across `transpile_cli`, `backend_registry_static`, and the selfhost/generated parser lanes, then fixed `.json` decode/encode as `json_adapter`, public raw-dict APIs plus selfhost seed helpers as `legacy_bridge`, signature/backend-spec/AST direct assembly as `compiler_internal`, and hook surfaces as the reserved `extern_hook` category.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] Fixed that P2 is not an `Any/object` removal plan but a typed-compiler-carrier plan, that JSON must converge on the `JsonValue` nominal lane, and that backend/runtime must not reinterpret `type_expr` or `dispatch_mode` semantics during the migration.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] Fixed the fields for `CompilerRootDocument`, `BackendSpecCarrier`, `LayerOptionsCarrier`, `EmitRequestCarrier`, `ModuleArtifactCarrier`, and `ProgramArtifactCarrier`; callables stay local implementation detail, while raw EAST/IR docs are treated as migration fields only until S3.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Made `src/toolchain/compiler/typed_boundary.py` the source of truth, moved host/static backend registries plus `ir2lang.py` / `py2x.py` onto typed-carrier-first paths, and shrank the old `dict[str, object]` surfaces to thin `to_legacy_dict()` adapters, a `load_east3_document_typed()` wrapper, and the writer boundary.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] Added native C++ `CompilerRootDocument` / `ResolvedBackendSpec` / `LayerOptionsCarrier` wrappers plus `*_typed()` APIs, then updated `selfhost/py2cpp.cpp` and `selfhost/py2cpp_stage2.cpp` to route through those wrappers and fall back to `to_legacy_dict()` only at the remaining legacy seams.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Moved module-root, leading-trivia, and bare-`Expr` assembly in `src/toolchain/ir/core.py` onto `_sh_make_*` builder helpers, and added the typed-carrier support shims (`CompilerRootDocument` re-coercion bypass plus `lower_ir_typed()` / `optimize_ir_typed()` / `emit_source_typed()`) needed to keep stage1 selfhost building.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_name_expr()` / `_sh_make_tuple_expr()` / `_sh_make_assign_stmt()` / `_sh_make_ann_assign_stmt()` and moved `with` bindings, typed bindings, tuple destructuring, class fields, and module top-level assign/annassign assembly through those helpers.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_constant_expr()` and moved the leaf `Constant` / `Name` / `Tuple` nodes from `_parse_primary()` / `_parse_comp_target()` through helpers too.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_ifexp_expr()` / `_sh_make_boolop_expr()` / `_sh_make_unaryop_expr()` / `_sh_make_compare_expr()` / `_sh_make_binop_expr()` and moved the `IfExp` / `BoolOp` / `UnaryOp` / `Compare` / `BinOp` nodes in both `ExprParser` and the lowered-expression path onto shared helpers.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added postfix/collection helpers such as `_sh_make_attribute_expr()` / `_sh_make_call_expr()` / `_sh_make_slice_node()` / `_sh_make_subscript_expr()` / `_sh_make_*_comp_expr()` / `_sh_make_*_expr()` and moved `ExprParser._parse_postfix()`, collection literals, generator/list/dict/set comprehensions, and `range(...)` normalization onto shared builders.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_arg_node()` / `_sh_make_lambda_expr()` / `_sh_make_formatted_value_node()` / `_sh_make_joined_str_expr()` and moved checked-in node assembly for lambda args/body plus f-string fragments onto shared builders.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_import_alias()` / `_sh_make_import*_stmt()` / `_sh_make_if_stmt()` / `_sh_make_for*_stmt()` / `_sh_make_while_stmt()` / `_sh_make_except_handler()` / `_sh_make_try_stmt()` and moved block-parser plus module-root import/control-flow assembly onto shared builders.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_function_def_stmt()` / `_sh_make_class_def_stmt()` and moved checked-in node assembly for nested functions, top-level functions, methods, and class roots onto shared builders.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_arg_node()` / `_sh_make_lambda_expr()` / `_sh_make_formatted_value_node()` / `_sh_make_joined_str_expr()` and moved lambda args, `Lambda`, f-string fragments, and module-level bare `Expr` statements onto shared helpers too.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_raise_stmt()` / `_sh_make_pass_stmt()` / `_sh_make_return_stmt()` / `_sh_make_yield_stmt()` / `_sh_make_augassign_stmt()` / `_sh_make_swap_stmt()` and moved simple-statement assembly in the statement-block and class-body parsers onto shared helpers too.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Applied `_sh_make_import_alias()` / `_sh_make_import_stmt()` / `_sh_make_import_from_stmt()` / `_sh_make_if_stmt()` / `_sh_make_while_stmt()` / `_sh_make_except_handler()` / `_sh_make_try_stmt()` / `_sh_make_for_stmt()` / `_sh_make_for_range_stmt()` to the real statement-block and module-root assembly paths.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_function_def_stmt()` / `_sh_make_class_def_stmt()` and moved checked-in direct assembly for nested/top-level/method `FunctionDef` nodes plus top-level `ClassDef` nodes onto shared helpers.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Moved the remaining string-literal-concatenation `BinOp` and default `ForRange` `Constant` nodes onto existing helpers too, clearing the last checked-in direct `kind` assembly left in `core.py` source-of-truth paths.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Moved concatenated-string `BinOp` assembly and the default `Constant` nodes used by `for ... in range(...)` onto helpers too, so checked-in direct AST node assembly in `src/toolchain/ir/core.py` is now confined to the helper definitions themselves.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Added `_sh_make_def_sig_info()` and routed `_sh_parse_def_sig()` through that helper so the raw signature-carrier dict is no longer assembled inline.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] With checked-in node construction in `src/toolchain/ir/core.py` now aligned on helper-owned builders, S3-01 is closed and the remaining object-carrier retreat work moves to the generated/selfhost runtime lanes in `S3-02`.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added module/class-root helpers to the generated C++ selfhost mirror and started routing the large top-level `FunctionDef` / `ClassDef` / `Import` / `ImportFrom`, class-field/method, top-level assignment, and bare-`Expr` `make_object` clusters through those builders. In parallel, the source-of-truth side gained `_sh_make_expr_token()` / `_sh_make_import_binding()` so token/import metadata carriers and mirror regressions use the same helper contract.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_expr_token()` and `_sh_make_import_binding()` so the source-of-truth tokenizer/import-metadata carriers now route through helpers instead of open-coded inline dict assembly.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_import_symbol_binding()` and `_sh_make_qualified_symbol_ref()` so the module-root import-resolution tail no longer assembles `import_symbols` / `qualified_symbol_refs` carriers inline.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_module_source_span()` / `_sh_make_import_resolution_meta()` / `_sh_make_module_meta()` so the remaining module-root carrier assembly inside `_sh_make_module_root()` now also routes through helpers.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Applied `_sh_make_import_symbol_binding()` across the pre-scan, import registration, and module parse paths so source-of-truth import-symbol metadata no longer uses raw dict assignment. `test_east_core.py` now guards that regression boundary, and the tracked selfhost test/docs were corrected so they no longer assume ignored mirror edits were part of the tracked slice.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Fixed `_sh_make_import_resolution_binding()` to merge only known resolution fields and aligned the binding-list type hints in `_sh_make_import_resolution_meta()` / `_sh_make_module_root()` with `dict[str, Any]`. The source guard now also rejects the old generic `resolution.items()` merge loop.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_lambda_arg_entry()` / `_sh_make_keyword_arg()` / `_sh_make_cast_entry()` so lambda parameter carriers, call keyword carriers, and numeric-promotion cast metadata now route through helper-owned builders too. `test_east_core.py` rejects the old raw `arg_entries.append(...)` / `keywords.append(...)` / `casts.append(...)` dict literals.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added a native-wrapper seam guard in `test_py2x_entrypoints_contract.py` so `make_object(...)` in `transpile_cli.cpp` / `backend_registry_static.cpp` is allowed only on the `to_legacy_dict()` and JSON-export seam lines.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_decl_meta()` so top-level function `runtime_abi_v1` / `template_v1` metadata and extern-var `extern_var_v1` metadata now share one helper-owned carrier instead of open-coded dict assembly.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_import_binding_fields()` / `_sh_make_import_resolution_binding()` so the module-root tail no longer chains `binding.get(...)` calls or `dict(binding)` when deriving `import_resolution_bindings`.
- Progress memo: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Added `_sh_make_arg_node()` / `_sh_make_lambda_arg_entry()` / `_sh_make_keyword_arg()` / `_sh_make_cast_entry()` to the generated C++ mirror so lambda args, call keywords, and numeric cast metadata no longer assemble open-coded `make_object` dicts inline. `test_prepare_selfhost_source.py` now also guards that boundary.

### P3: Harden compiler contracts and make stage / pass / backend handoffs fail closed

Context: [docs/ja/plans/p3-compiler-contract-hardening.md](../plans/p3-compiler-contract-hardening.md)

1. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01] Harden compiler contracts and make stage / pass / backend handoffs fail closed.
2. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] Inventory the current `check_east_stage_boundary`, `validate_raw_east3_doc`, and backend-entry guards, then classify blind spots that still go unchecked (`node shape`, `type_expr` / `resolved_type`, `source_span`, helper metadata).
3. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] Fix the responsibility boundary between schema validators, invariant validators, and backend-input validators so this plan does not overlap with `P1-EAST-TYPEEXPR-01` or `P2-COMPILER-TYPED-BOUNDARY-01`.
4. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] Extend `spec-dev` or equivalent design docs with required fields, allowed omissions, and diagnostic categories for EAST3 / linked output / backend input.
5. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] Fix the consistency rules and fail-closed policy for `type_expr` / `resolved_type` mirrors, `dispatch_mode`, `source_span`, and helper metadata.
6. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] Add central validator primitives around `toolchain/link/program_validator.py` and expand raw EAST3 / linked-output checks from coarse validation into node/meta invariant checks.
7. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] Add pre/post validation hooks to representative passes, lowering entrypoints, and linker entrypoints so malformed nodes stop propagating.
8. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] Run compiler-contract validators at representative backend entrypoints (first C++) and replace backend-local crashes or silent fallback with structured diagnostics.
9. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] Extend `tools/check_east_stage_boundary.py` or its successor guard so it can detect stage semantic-contract drift too.
10. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] Add representative unit/selfhost regressions so contract violations are reproducible as expected failures.
11. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] Refresh docs / TODO / archive / migration notes and fix the rule that validator updates are mandatory when new nodes/meta are introduced.

### P4: Canonicalize backend-registry metadata and strengthen selfhost parity gates

Context: [docs/ja/plans/p4-backend-registry-selfhost-parity-hardening.md](../plans/p4-backend-registry-selfhost-parity-hardening.md)

1. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01] Canonicalize backend-registry metadata and strengthen selfhost parity gates.
2. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] Inventory duplicated surfaces across `backend_registry.py` and `backend_registry_static.py` (backend spec, runtime copy, writer rules, option schema, direct-route behavior), then classify each difference as intentional or drift-prone.
3. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] Inventory current gates and blind spots across `build_selfhost`, stage2, direct e2e verification, and multilang selfhost tools, then fix the known-block vs regression classification policy in the decision log.
4. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] Define the canonical source of truth for backend capability, runtime-copy rules, option schema, and writer metadata so both host and static registries can be derived from it.
5. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] Fix the boundaries where intentional differences are allowed (for example host-only lazy imports or selfhost-only direct routes) together with their diagnostic contracts.
6. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] Move host/static registries toward shared metadata, a generator, or equivalent adapters and retire avoidable handwritten duplication.
7. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] Add a registry-drift guard or diff test so one-sided backend-surface updates fail fast.
8. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] Reorganize representative stage1 / stage2 / direct e2e / multilang selfhost parity suites so they report a stable shared summary and failure taxonomy.
9. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] Align unsupported / preview / known-block / regression diagnostics between registry code and parity reports so expected failures are explicitly managed.
10. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] Refresh docs / plan reports / archive so backend readiness, known blocks, and gate execution flow remain traceable.
11. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] Verify that representative internal changes are checked through equivalent contracts on both host and selfhost lanes, then fix reintroduction guards.

### P5: Full rollout of nominal ADTs as a language feature

Context: [docs/ja/plans/p5-nominal-adt-language-rollout.md](../plans/p5-nominal-adt-language-rollout.md)

1. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01] Carry out the full rollout of nominal ADTs as a language feature.
2. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] Inventory candidate language surfaces for nominal ADT declarations, constructors, variant access, and `match`, then decide on a selfhost-safe staged introduction path.
3. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] Fix the boundary between type-system base work, narrowing-base work, and full language-feature work so this plan does not overlap with `P1-EAST-TYPEEXPR-01`.
4. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] Extend `spec-east` / `spec-user` / `spec-dev` with nominal-ADT declaration surface, pattern nodes, match nodes, and diagnostic contracts.
5. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] Fix the static-check policy and error categories for exhaustiveness, duplicate patterns, and unreachable branches.
6. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] Update frontend and selfhost parser paths so they can accept representative nominal-ADT syntax.
7. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] Introduce ADT constructors, variant tests, variant projection, and `match` lowering into EAST/EAST3.
8. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] Verify through representative tests that built-in `JsonValue` and user-defined nominal ADTs use the same IR category.
9. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] Implement the minimal constructor / variant-check / destructuring / `match` path in a representative backend (first C++) and forbid silent fallback.
10. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] Organize rollout order and fail-closed policy for other backends, and fix diagnostics for unsupported targets.
11. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] Refresh selfhost / docs / archive / migration notes and close the full nominal-ADT rollout plan.
