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
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_code_emitter.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east3_optimizer.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_type.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
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

- [ ] [ID: P1-EAST-TYPEEXPR-01-S1-01] Inventory `split_union` / `normalize_type_name` / `resolved_type` string dependencies across frontend, lowering, optimizer, and backends, then classify them into `optional`, `dynamic union`, `nominal ADT`, and `generic container` usage.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S1-02] Lock the end state, non-goals, and migration order in the decision log so they remain consistent with archived `EAST123` and `JsonValue` contracts.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S2-01] Extend `spec-east` / `spec-dev` with `TypeExpr` schema, the three-way union classification, and the authority relationship between `type_expr` and `resolved_type`.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S2-02] Fix the IR contract that treats `JsonValue` as a nominal closed ADT rather than a generic union, including decode/narrowing responsibility and backend fail-closed rules.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S3-01] Update frontend type-annotation parsing to build `TypeExpr` from `int | bool`, `T | None`, and nested generic unions.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S3-02] Keep a migration `resolved_type` string mirror temporarily, but add validators and mismatch guards that treat `type_expr` as the source of truth.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S4-01] In `EAST2 -> EAST3`, distinguish optionals, dynamic unions, and nominal ADTs, and introduce instructions or metadata for narrowing / variant checks / decode helpers.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S4-02] Connect a representative `JsonValue` narrowing path (`as_obj/as_arr/as_int/...` or equivalent decode operations) through IR-first lowering rather than backend-local special cases.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S5-01] Use C++ as the first target and replace at least part of the current "general union -> object" path with fail-closed behavior or structured lowering.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S5-02] Audit other backends for `String/object` union fallbacks and align unsupported `TypeExpr` unions to explicit errors or guarded compatibility paths.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S6-01] Put a representative `JsonValue` lane on top of the new `TypeExpr` / nominal-ADT contract and verify that future runtime work can proceed IR-contract-first.
- [ ] [ID: P1-EAST-TYPEEXPR-01-S6-02] Refresh selfhost / unit / docs / archive and add guards against the reintroduction of stringly-typed union debt.

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
