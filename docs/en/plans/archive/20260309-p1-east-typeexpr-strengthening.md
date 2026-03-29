<a href="../../../ja/plans/archive/20260309-p1-east-typeexpr-strengthening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Structure EAST type representation and lift union / nominal ADT / narrowing out of string processing

Last updated: 2026-03-09

Related TODO:
- `ID: P1-EAST-TYPEEXPR-01` in `docs/ja/todo/index.md`

Background:
- The current EAST / emitter / optimizer stack still carries types mainly as strings such as `resolved_type: "int64|bool"`.
- String helpers like `split_union`, `normalize_type_name`, and `split_union_non_none` are spread across frontend, lowering, and backends, forcing optionals, dynamic unions, and nominal ADTs such as JSON through the same weak representation.
- As a result, composite types like `int|bool` can survive in annotations/EAST text, but later collapse into fallbacks such as `object` or `String`, losing IR-level meaning.
- `JsonValue` already exists as a public surface, but its current implementation still centers on raw `object` / `dict[str, object]` / `list[object]` wrappers rather than strong nominal-ADT lowering.
- If runtime/selfhost object carriers are cleaned up before this type debt is fixed in EAST, the semantic debt simply remains in string processing.

Goal:
- Introduce a structured `TypeExpr`-like representation into EAST so optionals, dynamic unions, nominal ADTs, and generic containers are carried as meaning rather than split strings.
- Create a foundation where closed nominal ADTs such as `JsonValue` are not treated as "just another union string".
- Move narrowing / variant checks / decode-helper semantics into IR-owned lowering instead of backend-local ad hoc logic.
- Stop backends from silently collapsing unsupported unions into `object` / `String` and replace that with fail-closed behavior or explicit nominal lowering.

Scope:
- `docs/ja/spec/spec-east.md` / `spec-dev.md` and, if needed, related runtime/type docs
- Frontend type-annotation parsing / type normalization / EAST construction
- Type and narrowing handling in `EAST2 -> EAST3` lowering
- Stringly-typed type helpers in backends/emitters/optimizers
- A representative `JsonValue` nominal-ADT lane
- Regression tests / guards / selfhost compatibility paths

Out of scope:
- Adding full Python pattern matching syntax
- Introducing arbitrary user-defined ADT source syntax in one shot
- Implementing general unions across all backends at once
- Removing the `make_object` overload family as part of this plan alone
- Removing the stage1 selfhost host-Python bridge at the same time

## Mandatory Rules

These are requirements, not recommendations.

1. A `resolved_type` string alone must not remain the source of truth. Type meaning must move to structured `TypeExpr`.
2. `T|None`, dynamic unions containing `Any/object`, and closed nominal ADTs such as `JsonValue` must be treated as separate categories.
3. Backends must not silently collapse unsupported unions into `object`, `String`, or similar fallbacks. If temporary compatibility remains, it must be guarded and scheduled for removal.
4. Narrowing / variant checks / JSON decode semantics belong to frontend/lowering/IR. Backends should only map IR instructions.
5. During migration, a string mirror may remain, but if it disagrees with `type_expr`, `type_expr` wins.
6. `JsonValue` must not be treated as a new spelling for generic dynamic fallback. It is a closed nominal ADT.
7. Any new type category must land with exact schema and examples in `spec-east` and unit tests in the same change.

Acceptance criteria:
- EAST/EAST3 carries a structured type representation able to distinguish optional, union, nominal ADT, and generic container categories.
- The frontend converts `int | bool`, `T | None`, and `JsonValue`-related types into structured representation instead of relying on string normalization.
- Lowering distinguishes dynamic unions from nominal ADTs and can express `JsonValue` decode / narrowing without backend-local fallback logic.
- At least one representative backend removes or fail-closes a current general-union fallback (`object` / `String`) path.
- Follow-up `JsonValue` nominal implementation can proceed IR-contract-first rather than runtime-first.

Planned verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_code_emitter.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east3_optimizer.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_type.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Implementation Order

Keep the order fixed. Do not deepen `JsonValue` runtime work first; stop the type-semantics debt in EAST before that.

1. Inventory stringly-typed type handling
2. Design `TypeExpr` schema and type categories
3. Generate `TypeExpr` in the frontend
4. Lower type / narrowing semantics into EAST3
5. Shrink backend fallbacks and make unsupported cases fail closed
6. Connect a representative `JsonValue` nominal-ADT lane
7. Lock specs / selfhost / guards

## Core Design Policy

### 1. Make `TypeExpr` the source of truth

It must distinguish at least:

- `NamedType(name)`
- `GenericType(base, args[])`
- `OptionalType(inner)`
- `UnionType(options[])`
- `DynamicType(kind=Any|object|unknown)`
- `NominalAdtType(name, variants|tag_domain)` or equivalent metadata

Notes:
- The exact serialized JSON shape can be decided during implementation, but it must not degrade back into backend-specific type strings.
- During migration, a `resolved_type` string mirror may remain, but `type_expr` is authoritative.

### 2. Split unions into three lanes

- optional:
  - `T | None`
- dynamic union:
  - unions that contain `Any/object/unknown`
- nominal closed union:
  - ADTs such as `JsonValue` whose variant domain is fixed by spec

These must not share one lowering rule.

### 3. Treat JSON as a nominal ADT, not as a generic union

- Do not push `int|bool|str|dict[...]|list[...]` into backends as a generic union model for JSON.
- Recognize `JsonValue` as a dedicated nominal surface at the IR layer.
- Full nominalization of `std/json.py` is a later implementation slice, but the type contract it depends on belongs in this P1.

### 4. Default to fail-closed backends

- If a target cannot yet represent general unions such as `int|bool`, it must not silently escape to `object` or `String`.
- Any temporary compatibility fallback must be documented with guards and removal steps.

## Breakdown

- [x] [ID: P1-EAST-TYPEEXPR-01-S1-01] Inventory `split_union` / `normalize_type_name` / `resolved_type` string dependencies across frontend, lowering, optimizer, and backends, then classify them into `optional`, `dynamic union`, `nominal ADT`, and `generic container` usage.
- [x] [ID: P1-EAST-TYPEEXPR-01-S1-02] Lock the end state, non-goals, and migration order in the decision log so they remain consistent with archived `EAST123` and `JsonValue` contracts.
- [x] [ID: P1-EAST-TYPEEXPR-01-S2-01] Extend `spec-east` / `spec-dev` with `TypeExpr` schema, the three-way union classification, and the authority relationship between `type_expr` and `resolved_type`.
- [x] [ID: P1-EAST-TYPEEXPR-01-S2-02] Fix the IR contract that treats `JsonValue` as a nominal closed ADT rather than a generic union, including decode/narrowing responsibility and backend fail-closed rules.
- [x] [ID: P1-EAST-TYPEEXPR-01-S3-01] Update frontend type-annotation parsing to build `TypeExpr` from `int | bool`, `T | None`, and nested generic unions.
- [x] [ID: P1-EAST-TYPEEXPR-01-S3-02] Keep a migration `resolved_type` string mirror temporarily, but add validators and mismatch guards that treat `type_expr` as the source of truth.
- [x] [ID: P1-EAST-TYPEEXPR-01-S4-01] In `EAST2 -> EAST3`, distinguish optionals, dynamic unions, and nominal ADTs, and introduce instructions or metadata for narrowing / variant checks / decode helpers.
- [x] [ID: P1-EAST-TYPEEXPR-01-S4-02] Connect a representative `JsonValue` narrowing path (`as_obj/as_arr/as_int/...` or equivalent decode operations) through IR-first lowering rather than backend-local special cases.
- [x] [ID: P1-EAST-TYPEEXPR-01-S5-01] Use C++ as the first target and replace at least part of the current "general union -> object" path with fail-closed behavior or structured lowering.
- [x] [ID: P1-EAST-TYPEEXPR-01-S5-02] Audit other backends for `String/object` union fallbacks and align unsupported `TypeExpr` unions to explicit errors or guarded compatibility paths.
- [x] [ID: P1-EAST-TYPEEXPR-01-S6-01] Put a representative `JsonValue` lane on top of the new `TypeExpr` / nominal-ADT contract and verify that future runtime work can proceed IR-contract-first.
- [x] [ID: P1-EAST-TYPEEXPR-01-S6-02] Refresh selfhost / unit / docs / archive and add guards against the reintroduction of stringly-typed union debt.

## Implementer Notes

### S1 must explicitly produce

- Which helpers are really optional-only
- Which helpers exist only because unions containing `Any/object` are treated as dynamic
- Which helpers are incorrectly collapsing JSON-like nominal ADTs into generic unions

### S2 must not leave ambiguous

- How nodes without `type_expr` are handled
- How long the `resolved_type` string mirror survives
- Whether `JsonValue` is represented as `UnionType` or as a dedicated nominal category

### S4 should touch first

- optional detection
- runtime-boundary detection for unions containing `Any/object`
- narrowing equivalent to `JsonValue` decode helpers

### S5 must forbid

- Declaring C++ support while `int|bool -> object` remains an untracked silent fallback
- Turning Rust-style `int|bool -> String` degradation into a canonical contract

Decision log:
- 2026-03-09: Added this P1 in response to the user request to prioritize EAST strengthening over runtime-first `std/json.py` nominalization.
- 2026-03-09: Fixed the main focus of this P1 on making `TypeExpr` authoritative so optionals, dynamic unions, and nominal ADTs are distinguished in IR.
- 2026-03-09: Fixed the policy that existing `JsonValue` public surface remains useful, but it must not be prolonged as a generic-union runtime wrapper; it should converge toward a closed nominal ADT.
- 2026-03-09: The `S1-01` frontend / selfhost-parser inventory confirmed that `toolchain/frontends/transpile_cli.py:523` keeps unions as raw strings in `normalize_param_annotation()`, while `toolchain/ir/core.py:219` turns `Optional[T]` into the string `"T | None"` and `toolchain/ir/core.py:118` / `2952` use `_sh_is_type_expr_text()` / `_split_union_types()` to support type aliases and object/Any receiver guards. This is the primary mixing point between `optional` and `dynamic union`.
- 2026-03-09: The `S1-01` lowering inventory confirmed that `toolchain/ir/east2_to_east3_lowering.py:27` / `35` / `90` use `_normalize_type_name()` / `_split_union_types()` / `_is_any_like_type()` to detect only whether a union contains `Any/object/unknown`, and then `east2_to_east3_lowering.py:474` feeds that result directly into `Box/Unbox` boundaries. General unions and dynamic unions are therefore collapsed at the IR entrance.
- 2026-03-09: The `S1-01` generic-container inventory confirmed that `toolchain/link/runtime_template_specializer.py:67` carries its own `_parse_type_expr()` / `_type_expr_to_string()` path and reparses `annotation/return_type/resolved_type`, duplicating `backends/common/emitter/code_emitter.py:1516` / `1594` / `1757` (`split_union()` / `split_union_non_none()` / `normalize_type_name()`). Generic containers and template specialization still depend on `resolved_type` strings as the source of truth.
- 2026-03-09: The `S1-01` backend inventory confirmed that C++ (`backends/cpp/emitter/type_bridge.py:372`, `backends/cpp/emitter/header_builder.py:1130`) lowers only optionals structurally and collapses the remaining general unions to `object`; Rust (`backends/rs/emitter/rs_emitter.py:1973`) maps any-like unions to `PyAny`, optionals to `Option<T>`, and multi-arm unions to `String`; C# (`backends/cs/emitter/cs_emitter.py:676`) also collapses non-optional unions to `object`. `JsonValue` remains represented by fallback and decode-first guards instead of a nominal ADT contract.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: To stay aligned with archived `p0-east123-staged-ir.md`, the end state keeps `EAST3` as the single semantics-level source of truth. `type_expr` may still be absent or unstructured in parser-near `EAST1`, but it must be structured by normalized `EAST2`, and no lowering/optimizer/linker/backend stage after that may recover type meaning by reparsing `resolved_type`. During migration, `resolved_type` survives only as a mirror for legacy readers, with `type_expr` always taking precedence.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: To stay aligned with archived `20260308-p1-jsonvalue-decode-first-contract.md` and `spec-runtime`, `JsonValue` is not treated as an open general union such as `int|float|str|dict[...]|list[...]`. It stays a nominal closed ADT lane with a decode-first public surface. P1 only lifts that nominal category into IR/`TypeExpr`; full `std/json.py` nominal carrier work, compiler/selfhost typed-boundary work, and user-defined ADT syntax or `match`/exhaustiveness remain follow-up work in `P2` / `P5`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: Three non-goals are fixed. (1) Do not implement general unions across every backend in one pass. (2) Do not delete `resolved_type` everywhere at the start of migration. (3) Do not combine this plan with full runtime-side `object` / `make_object` retirement or host-Python selfhost bridge removal. P1 completes when schema, validators, lowering, and representative backend fail-closed behavior are in place; it does not include the final runtime carrier form or full language rollout.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: The migration order is fixed as follows. Step 1: `S2` specifies the `TypeExpr` schema, the three union categories, and the authority rule `type_expr > resolved_type`. Step 2: `S3` makes the frontend emit `type_expr` and demotes `resolved_type` to a mirror protected by mismatch guards. Step 3: `S4` makes EAST3 lowering split `optional`, `dynamic union`, and `nominal ADT` into separate lanes and connect `JsonValue` narrowing through IR-first lowering. Step 4: `S5` makes a representative backend replace silent fallback with fail-closed behavior or structured lowering. Step 5: `S6` locks the representative `JsonValue` lane and reintroduction guards, after which internal typed-boundary work continues in `P2` and full nominal-ADT language rollout continues in `P5`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-01]: Added expression/function-level `type_expr` / `arg_type_exprs` / `return_type_expr`, the `NamedType/GenericType/OptionalType/UnionType/DynamicType/NominalAdtType` schema, the three-way union split, and the `type_expr > resolved_type` mirror rule to `spec-east`. The EAST2 neutral contract now treats `OptionalType`, dynamic unions, and nominal ADTs as distinct categories, and explicitly forbids `EAST2 -> EAST3` from recovering semantics by re-splitting `resolved_type`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-01]: Added the `TypeExpr` implementation contract to `spec-dev`, fixing that frontend/validator/lowering/template-specializer/backend helpers must treat `type_expr` as canonical, that unsupported general-union fallbacks to `object` / `String` are only temporary compatibility guarded by removal plans, and that any path trying to emit a nominal ADT as a general union must stop with `semantic_conflict` / `unsupported_syntax`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-02]: Added the `JsonValue` nominal closed-ADT lane to `spec-east`, fixing `json.loads`, `json.loads_obj`, `json.loads_arr`, `json.value.as_*`, `json.obj.get_*`, and `json.arr.get_*` as canonical semantic tags. `JsonValue` / `JsonObj` / `JsonArr` must now stay as `NominalAdtType` and must not be expanded into a general union or `object` fallback.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-02]: Fixed decode/narrowing responsibility on the frontend/lowering/validator side and forbade backends/hooks from reconstructing JSON decode semantics from raw callee names, attribute names, or `resolved_type` strings. Targets that still lack a `JsonValue` nominal carrier or decode-op mapping must fail closed instead of degrading to `object`, `PyAny`, or `String`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-01]: Added `toolchain/frontends/type_expr.py` as the shared parser/stringifier and moved `transpile_cli.py`, `signature_registry.py`, and `toolchain/ir/core.py` onto the same `parse_type_expr_text()` / `normalize_type_text()` / `type_expr_to_string()` contract. Quoted annotations, `int | bool`, `typing.Optional[T]`, nested generic unions, and `JsonValue` nominal ADTs now normalize to the same `TypeExpr` in both frontend and selfhost lanes.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-01]: Updated the selfhost parser to emit `FunctionDef.arg_type_exprs` / `return_type_expr`, `AnnAssign.annotation_type_expr` / `decl_type_expr`, and typed `Name.type_expr`, and taught `tools/prepare_selfhost_source.py` to inline the shared `TypeExpr` helper into selfhost support blocks. Verified with `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/frontends/transpile_cli.py src/toolchain/frontends/signature_registry.py src/toolchain/ir/core.py tools/prepare_selfhost_source.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py' -k quoted_type_annotation_is_normalized`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py' -k type_expr_is_emitted_for_union_optional_and_nested_generic_annotations`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py' -k type_expr_is_built_for_union_optional_and_nominal_annotations`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k normalize_param_annotation_coarse_types`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k extract_function_signatures_from_python_source_parses_defs`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_stdlib_signature_registry.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_self_hosted_signature.py'`, and `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: Completed `sync_type_expr_mirrors()` as a generic mirror filler / mismatch guard that also covers `type_expr -> resolved_type`, while treating `unknown` as a migration-only placeholder that may be auto-filled. Running the same guard from `toolchain/ir/east_io.py`, `east2.py`, `east3.py`, and `link/program_validator.py` makes loaded, normalized, and validated documents fail fast when their legacy string mirrors drift away from frontend/selfhost-generated `TypeExpr`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: Added `test_frontend_type_expr.py` to lock three things: (1) `type_expr` fills `resolved_type` / `annotation` / `decl_type` / `arg_types` / `return_type`, (2) concrete mirror mismatches raise `RuntimeError`, and (3) `normalize_east1_to_east2_document()` and `validate_raw_east3_doc()` share the same guard. Verified with `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/frontends/transpile_cli.py src/toolchain/frontends/signature_registry.py src/toolchain/ir/core.py tools/prepare_selfhost_source.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_frontend_type_expr.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_stdlib_signature_registry.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_self_hosted_signature.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k any_basic_runtime`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k any_dict_items_runtime`, `python3 tools/check/check_todo_priority.py`, and `git diff --check`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: Added `sync_type_expr_mirrors()` to `toolchain/frontends/type_expr.py` so it now synchronizes and validates the legacy mirrors `type_expr -> resolved_type`, `annotation_type_expr -> annotation`, `decl_type_expr -> decl_type`, `return_type_expr -> return_type`, and `arg_type_exprs[*] -> arg_types[*]` in one pass. Missing, blank, or `unknown` mirrors are backfilled from `type_expr`; any real mismatch stops with a path-qualified `RuntimeError`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: Extended the mismatch guard to the selfhost output finalizer (`toolchain/ir/core.py`), the `EAST1 -> EAST2` normalizer (`toolchain/ir/east2.py`), the generic EAST root loader (`toolchain/ir/east_io.py`), frontend `load_east3_document()` (`toolchain/ir/east3.py`), and the linker raw-EAST3 gate (`toolchain/link/program_validator.py`). This keeps legacy `resolved_type` readers such as `runtime_template_specializer.py` behind a fail-fast mirror check. Verified with `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/ir/core.py src/toolchain/ir/east2.py src/toolchain/ir/east3.py src/toolchain/ir/east_io.py src/toolchain/link/program_validator.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_frontend_type_expr.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py' -k type_expr`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py' -k load_east3_document_helper_lowers_from_json_input`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py' -k load_east3_document_normalizes_existing_forcore_runtime_dispatch_mode`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k normalize_param_annotation_coarse_types`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_self_hosted_signature.py'`, and `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S4-01]: Updated `frontend_semantics.py`, `signature_registry.py`, and `toolchain/ir/core.py` so `pytra.std.json.loads(_obj/_arr)` and the `JsonValue/JsonObj/JsonArr` decode helpers now land in the `json.*` semantic-tag family. In `toolchain/ir/east2_to_east3_lowering.py`, boundary classification now prefers `decl_type_expr` / `annotation_type_expr` / target `type_expr`, and representative lanes now carry `type_expr_summary_v1` and `json_decode_v1` metadata so EAST3 can distinguish optionals, dynamic unions, and nominal ADTs without backend-local reinterpretation. Verified with `python3 -m py_compile src/toolchain/frontends/frontend_semantics.py src/toolchain/frontends/signature_registry.py src/toolchain/frontends/type_expr.py src/toolchain/ir/core.py src/toolchain/ir/east2_to_east3_lowering.py tools/unittest/ir/test_east_core.py tools/unittest/ir/test_east2_to_east3_lowering.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_frontend_type_expr.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`, and `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k json`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S4-02]: Promoted the representative `JsonValue.as_obj()` lane into `Call.lowered_kind=JsonDecodeCall` plus `json_decode_receiver`, with `json_decode_v1.ir_category=JsonDecodeCall` marking it as an IR-first narrowing path. The C++ backend now renders that lane from `semantic_tag + lowered_kind + json_decode_receiver` instead of reinterpreting raw method names. Verified with `python3 -m py_compile src/toolchain/ir/east2_to_east3_lowering.py src/backends/cpp/emitter/call.py tools/unittest/ir/test_east2_to_east3_lowering.py tools/unittest/emit/cpp/test_east3_cpp_bridge.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k json`, `python3 tools/check/check_todo_priority.py`, and `git diff --check`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S5-01]: The representative C++ fail-closed lane was narrowed first to `AnnAssign` / `FunctionDef` signatures that already carry structured `TypeExpr`. `backends/cpp/emitter/type_bridge.py` now stops on nested general unions with `unsupported_syntax`, and `stmt.py` / `cpp_emitter.py` now prefer `annotation_type_expr` / `decl_type_expr` / `arg_type_exprs` / `return_type_expr` before type rendering. This means lanes such as `int|bool` and `list[int|bool]` no longer silently collapse to `object` as long as `TypeExpr` is present. Verified with `python3 -m py_compile src/backends/cpp/emitter/type_bridge.py src/backends/cpp/emitter/stmt.py src/backends/cpp/emitter/cpp_emitter.py tools/unittest/emit/cpp/test_cpp_type.py tools/unittest/emit/cpp/test_east3_cpp_bridge.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_type.py'`, and `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S5-02]: The cross-backend inventory confirmed Rust `String` fallback, C# `object` fallback, and Go/Java/Kotlin/Scala/Swift/Nim `any/Object/Any/auto` fallback for unsupported general unions. The existing Rust/C# local TypeExpr guards stay in place, and the remaining Go/Java/Kotlin/Scala/Swift/Nim backends now share `reject_backend_general_union_type_exprs()` at their entry points so general-union `TypeExpr` fails closed with `unsupported_syntax`. JS/TS/PHP/Ruby/Lua remain compatibility targets for now because they already live on dynamic host carriers; their ADT/runtime contract work stays separate. Verified with `python3 -m py_compile src/backends/common/emitter/code_emitter.py src/backends/go/emitter/go_native_emitter.py src/backends/java/emitter/java_native_emitter.py src/backends/kotlin/emitter/kotlin_native_emitter.py src/backends/scala/emitter/scala_native_emitter.py src/backends/swift/emitter/swift_native_emitter.py src/backends/nim/emitter/nim_native_emitter.py tools/unittest/emit/cpp/test_noncpp_east3_contract_guard.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_noncpp_east3_contract_guard.py'`, `python3 tools/check/check_todo_priority.py`, and `git diff --check`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S6-01]: Kept the representative lane fixed to `json.value.as_obj`, but moved semantic inference off `owner_type == "JsonValue"` and onto `TypeExpr`/nominal summaries. `summarize_type_expr()` now carries `nominal_adt_name`, `json_decode_v1` now records `receiver_nominal_adt_name`, and a new regression proves the lane still lowers when `resolved_type="unknown"` but `type_expr=JsonValue` is present. The migration-only compat path is now also labeled explicitly as `contract_source=resolved_type_compat`. The inverse mismatch now stops with `json_decode_contract_violation` when `semantic_tag=json.value.as_obj` disagrees with the receiver nominal name. This keeps later runtime nominalization work anchored on IR metadata instead of raw method names or string mirrors. Verified with `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/ir/east2_to_east3_lowering.py tools/unittest/common/test_frontend_type_expr.py tools/unittest/ir/test_east2_to_east3_lowering.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_frontend_type_expr.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_pylib_json.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`, `python3 tools/check/check_todo_priority.py`, and `git diff --check`.
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S6-02]: Expanded the reintroduction guard beyond the representative lane to cover `json.obj.get_int`, `json.arr.get_bool`, and `json.loads_obj`, locking `receiver_nominal_adt_name`, `result_type.nominal_adt_name`, and `decode_kind=module_load` in `tools/check/check_jsonvalue_typeexpr_contract.py`. The tool import path was normalized to `toolchain.*` so it stays stable both from repo-root execution and selfhost-adjacent module layouts. In parallel, `test_east2_to_east3_lowering.py` now runs the guard script directly, and `test_prepare_selfhost_source.py` now locks the selfhost seed's `_JSON_NOMINALS` / `NominalAdtType` helper path. Verified with `python3 tools/check/check_jsonvalue_typeexpr_contract.py`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_jsonvalue_typeexpr_contract.py'`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east2_to_east3_lowering.py' -k json`, `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`, `python3 tools/build_selfhost.py`, `python3 tools/check/check_todo_priority.py`, and `git diff --check`.
