# P3: Harden Compiler Contracts and Make Stage / Pass / Backend Handoffs Fail Closed

Last updated: 2026-03-11

Related TODO:
- `ID: P3-COMPILER-CONTRACT-HARDENING-01` in `docs/ja/todo/index.md`

Background:
- Even if `P1-EAST-TYPEEXPR-01` and `P2-COMPILER-TYPED-BOUNDARY-01` improve type semantics and carrier boundaries, the compiler can still decay if internal handoff contracts remain weak. In that case, breakage leaks downstream as backend-local crashes or silent fallback.
- Some guards already exist, but they are still too coarse. For example, `tools/check_east_stage_boundary.py` prevents cross-stage imports/calls, but it does not validate node shape or `meta` / `source_span` / type invariants.
- `validate_raw_east3_doc(...)` in `toolchain/link/program_validator.py` also focuses on coarse contracts such as `kind`, `east_stage`, `schema_version`, and `dispatch_mode`. It does not yet guarantee node-level invariants or post-pass consistency.
- As a result, optimizers, lowerers, and backends often assume required fields locally, and schema drift is discovered late during feature work or selfhost transitions.
- If Pytra is going to prioritize internal compiler improvement, it needs machine-checkable contracts for what each stage may accept and return before adding more language surface.

Goal:
- Define and enforce EAST3 / linked-program / backend handoff contracts through validators and guards, and make them fail closed.
- Fix minimum invariants at stage, pass, and backend-entry boundaries so silent fallback and malformed payload forwarding stop being normal behavior.
- Improve diagnostics so crashes can be traced through `source_span`, category, and offending node kind.
- Make sure the `TypeExpr` / typed-carrier work from P1/P2 does not become "added but never validated."

Scope:
- `toolchain/ir/east3.py` / `toolchain/link/program_validator.py` / `toolchain/link/global_optimizer.py`
- `toolchain/ir/east2_to_east3_lowering.py` and representative EAST3 optimization passes
- `tools/check_east_stage_boundary.py` and compiler contract guards
- Representative backend entrypoints (first C++) and the IR/EAST contracts they consume
- Diagnostics / regression tests / selfhost-facing guards

Out of scope:
- The detailed `TypeExpr` schema or nominal-ADT semantics themselves
- Typed-carrier migration itself
- New user-facing syntax or new language features
- Full contract coverage for every backend at once
- Runtime-helper behavior changes as the primary target

Dependencies:
- The `type_expr` source-of-truth policy from `P1-EAST-TYPEEXPR-01` must at least be fixed
- The typed-carrier / adapter-seam policy from `P2-COMPILER-TYPED-BOUNDARY-01` must at least be fixed

## Mandatory Rules

These are requirements, not recommendations.

1. Any document consumed by a pass, backend, or linker must have a validator that defines both schema and invariants. Hidden assumptions are not enough.
2. Validators must reject missing fields, type mismatches, and contradictory metadata in fail-closed mode. They must not silently escape into `unknown` or fallback paths.
3. `source_span`, `repr`, and diagnostic categories must not be silently dropped for nodes that are expected to carry them. If absence is allowed, the contract must say why.
4. Ownership of `TypeExpr` / `resolved_type` / `dispatch_mode` / helper metadata must be defined centrally, not by backend-local interpretation.
5. Stage-boundary guards must validate semantic boundaries too, not only import/call boundaries.
6. Any new node kind, meta key, or helper protocol must ship with validator coverage and representative tests in the same change.
7. Backend entrypoints must not "do their best" with malformed IR. Contract violations must be reported as explicit diagnostics.

Acceptance criteria:
- Validators exist for raw EAST3, linked output, and representative backend input, and they cover at least basic node-level invariants.
- Representative mismatches in `TypeExpr` / `resolved_type` / `source_span` / `meta` stop through structured diagnostics instead of backend crashes.
- `tools/check_east_stage_boundary.py` or an equivalent guard covers stage semantic contracts too.
- Representative optimize/lowering/backend entrypoints run validator hooks and do not silently pass malformed documents through.
- Regression coverage exists so later P4/P5 work does not casually reintroduce contract drift.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_east_stage_boundary.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_program_validator.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Implementation Order

Keep the order fixed: first expose the blind spots, then add central validators, then wire them into representative backend/selfhost gates.

1. Inventory current validators / guards / blind spots
2. Fix compiler contracts and non-goals
3. Introduce central validator primitives
4. Wire them into passes / linker / backend entrypoints
5. Strengthen diagnostics / tests / guards
6. Refresh docs / archive / migration notes

## S1 Inventory Results

### Current guard / validator coverage

| Area | What it currently validates | What it does not validate yet |
| --- | --- | --- |
| `tools/check_east_stage_boundary.py` | Cross-stage import/call boundaries for `east2.py` and `code_emitter.py` | Document shape, `type_expr` / `resolved_type` mirrors, `source_span` / `repr`, helper metadata, semantic drift at pass/backend entry |
| `validate_raw_east3_doc(...)` | Top-level `kind=Module`, `east_stage=3`, `body` list, `schema_version>=1`, `meta.dispatch_mode`, forbidding `meta.linked_program_v1`, and `sync_type_expr_mirrors(...)` | Recursive node shape, node-level `source_span` / `repr` requirements, helper-metadata categories, node/meta `dispatch_mode` consistency, post-pass drift |
| `validate_link_input_doc(...)` | Manifest-level schema plus required `target` / `dispatch_mode` / `entry_modules` / `modules` fields | Per-module EAST3 payload shape and semantic contract for options payload |
| `validate_link_output_doc(...)` | Manifest-level schema, helper-module metadata presence, and top-level required `global` / `diagnostics` keys | Internal shape of `global`, invariant checks for embedded IR/EAST artifacts, schema for diagnostic items |
| `program_loader.py` | `validate_raw_east3_doc(...)` at raw EAST3 load time | Revalidation after optimizer/linker/template-specialization mutations |
| `backend_registry.py` / `backend_registry_static.py` | Backend spec, option schema, and typed-carrier coercion | IR contract at `lower_ir_typed` / `optimize_ir_typed` / `emit_source_typed` / `emit_module_typed`. The host lane can still surface backend-local failures through `suppress_exceptions=True` fallback behavior |

### Blind-spot categories

- `node shape`
  - Raw EAST3 validation stops at top-level `Module`; representative node kinds still lack central required-field / field-type / child-shape checks.
- `type_expr` / `resolved_type`
  - Mirror syncing exists, but canonical ownership by stage, acceptable `unknown` lanes, and backend-entry requirements are not fixed yet.
- `source_span` / `repr`
  - Required versus optional nodes are not defined centrally, so missing spans leak into backend crashes or poor diagnostics.
- `helper metadata`
  - Runtime helper, linked helper, and dispatch-helper `meta` keys still depend on producer/consumer conventions rather than a central validator.
- `stage semantic drift`
  - `check_east_stage_boundary.py` only polices imports/calls and does not cover semantic drift across `east2 -> east3 -> linked output -> backend input`.
- `backend input`
  - Representative backend entrypoints still lack compiler-contract validators, so malformed IR surfaces as backend-local exceptions or silent fallback.

## S1 Responsibility Boundaries

- `schema validator`
  - Scope: serialization/container shape for raw EAST3, linked input, linked output, and backend-input artifacts.
  - Responsibility: required top-level fields, enum domains, list/object shape, helper-module top-level metadata, and syntactic `type_expr` mirror consistency.
  - Out of scope: node-level semantic invariants and target-specific backend assumptions.

- `invariant validator`
  - Scope: EAST3 / linked output / representative IR after schema validation.
  - Responsibility: per-node required fields, `source_span` / `repr` preservation contracts, `dispatch_mode` / `resolved_type` / helper-metadata consistency, and post-pass relationships that must remain true.
  - Out of scope: backend-specific lowering detail and emit strategy.

- `backend input validator`
  - Scope: immediately before representative backend entrypoints (first C++).
  - Responsibility: convert target-local unsupported lowered kinds, required metadata, and malformed backend inputs into structured diagnostics.
  - Out of scope: raw-doc coercion and carrier migration; that remains P2 territory.

### Boundary vs. P1 / P2

- `P1-EAST-TYPEEXPR-01`
  - Owns the `TypeExpr` schema and mirror format. P3 only validates adherence to that canonical contract.
- `P2-COMPILER-TYPED-BOUNDARY-01`
  - Owns carrier and adapter seams. P3 makes the document / IR contracts fail-closed after those seams.
- `P3`
  - Owns machine-checkable rules for what each stage may accept and return. It does not add new carriers or language surface.

## Breakdown

- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] Inventory current `check_east_stage_boundary`, `validate_raw_east3_doc`, and backend-entry guards, then classify blind spots that are still unchecked (`node shape`, `type_expr` / `resolved_type`, `source_span`, helper metadata).
- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] Fix the responsibility boundary between schema validation, invariant validation, and backend-input validation so this plan does not overlap with `P1-EAST-TYPEEXPR-01` or `P2-COMPILER-TYPED-BOUNDARY-01`.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] Extend `spec-dev` or equivalent design docs with required fields, allowed omissions, and diagnostic categories for EAST3 / linked output / backend input.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] Fix consistency rules and fail-closed policy for `type_expr` / `resolved_type` mirrors, `dispatch_mode`, `source_span`, and helper metadata.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] Add central validator primitives around `toolchain/link/program_validator.py` and expand raw EAST3 / linked-output checks beyond coarse schema validation into node/meta invariants.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] Add pre/post validation hooks to representative passes, lowering entrypoints, and linker entrypoints so malformed nodes stop propagating.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] Run compiler-contract validators at representative backend entrypoints (first C++) and replace backend-local crashes or silent fallback with structured diagnostics.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] Extend `tools/check_east_stage_boundary.py` or its successor guard so it can detect stage semantic-contract drift too.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] Add representative unit/selfhost regressions so contract violations can be reproduced as expected failures.
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] Refresh docs / TODO / archive / migration notes and fix the rule that validator updates are mandatory when new nodes/meta are introduced.

## Expected Deliverables

### Deliverables for S1

- An inventory of what current validators/guards do and do not validate
- A clear split between `schema`, `invariant`, and `backend input` validation layers

### Deliverables for S2

- Ownership rules for `TypeExpr` / `resolved_type` / `source_span` / `meta`
- A list of mismatches that must fail closed

### Deliverables for S3

- Central validator helpers
- Validator hooks at representative pass / linker / backend boundaries

### Deliverables for S4

- Representative cases that stop with diagnostics rather than backend crashes
- A new or strengthened semantic-boundary guard

### Deliverables for S5

- Regression coverage that detects contract drift
- Docs/archive guidance that makes validator updates hard to forget

Decision log:
- 2026-03-09: Added this P3 in response to the user request to prioritize compiler-internal strengthening after the type and carrier groundwork.
- 2026-03-09: Fixed the scope of this P3 to validators and fail-closed contracts at stage / pass / backend handoffs, not new language features.
- 2026-03-09: Fixed the policy that boundary guards such as `check_east_stage_boundary` must grow beyond import/call policing and cover semantic invariants too.
- 2026-03-11: `S1-01` inventory confirmed that current guards are still biased toward top-level schema checks and import/call policing, while node shape, `source_span`, helper metadata, and backend-input contracts remain largely unvalidated.
- 2026-03-11: `S1-02` fixed a three-layer responsibility split: schema validators own serialization/container shape, invariant validators own node/meta relationships, and backend-input validators own target-local fail-closed diagnostics.
