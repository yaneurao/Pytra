<a href="../../../ja/plans/archive/20260311-p5-nominal-adt-language-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P5: Full rollout of nominal ADTs as a language feature

Last updated: 2026-03-11

Related TODO:
- `ID: P5-NOMINAL-ADT-ROLLOUT-01` in `docs/ja/todo/index.md`

Background:
- To handle closed nominal ADTs such as `JsonValue` cleanly, Pytra first needs structured `TypeExpr`, union classification, and narrowing contracts in EAST/IR.
- That base belongs to `P1-EAST-TYPEEXPR-01`. If user-facing nominal-ADT language features land before that, backend-specific special cases and `object` fallbacks will multiply again.
- In the long run, however, Pytra still needs more than built-in nominal ADTs: user-defined closed ADTs, constructors, variant projection, `match`, and exhaustiveness checking.
- Those belong after the type base, selfhost support, representative backend implementation, and runtime contracts are in place, so they should sit later than the current unfinished P0/P1/P2 work.

Goal:
- Introduce nominal ADTs as an official Pytra language feature.
- Define user-defined ADTs, constructors, variant checks/projections, `match`, and exhaustiveness checking as language-wide contracts rather than backend tricks.
- Make built-in nominal ADTs such as `JsonValue` and future user-defined ADTs converge on the same IR / lowering / backend contract.

Scope:
- Source syntax or equivalent declaration surface for nominal ADTs
- Constructors / variants / destructuring / `match`
- Static checking for exhaustiveness / unreachable branches / duplicate patterns
- ADT, pattern, and match nodes in EAST/EAST3
- Representative backend codegen/runtime contracts
- Selfhost parser / frontend / docs / tests

Out of scope:
- The type-system base handled by `P1-EAST-TYPEEXPR-01`
- Compiler-internal carrier cleanup handled by `P2-COMPILER-TYPED-BOUNDARY-01`
- Immediate full support on all targets
- Requiring fully Python-identical ADT/match syntax from day one
- Ad hoc rescue paths through exceptions, dynamic casts, or reflection

Dependencies:
- `P1-EAST-TYPEEXPR-01` completed, or at least its `TypeExpr` / nominal-ADT / narrowing contracts fixed
- `P2-COMPILER-TYPED-BOUNDARY-01` policy fixed for compiler-internal carrier cleanup
- A representative backend already running a nominal `JsonValue` lane

## Mandatory Rules

1. A nominal ADT must not be sugar for `object` fallback. The IR must identify it as a closed-variant type.
2. ADT constructors, variant access, and `match` belong to frontend/lowering/IR ownership, not backend-local special cases.
3. Exhaustiveness checking may be staged, but the IR/diagnostic design must at least be able to express non-exhaustive, duplicate-pattern, and unreachable-branch states.
4. Built-in nominal ADTs (for example `JsonValue`) and user-defined nominal ADTs must converge on one node/category family rather than separate feature tracks.
5. Unsupported ADT/pattern paths in backends must fail closed instead of silently falling back.
6. Syntax that the selfhost parser cannot read must not be promoted as canonical without a staged introduction surface.

Acceptance criteria:
- The declaration surface, constructors, variant access, `match`, and static-checking policy for nominal ADTs are fixed in docs/spec.
- Built-in ADTs and user-defined ADTs can be represented through the same IR category.
- A representative backend passes a minimal end-to-end path for constructors, variant checks, destructuring, and `match`.
- The selfhost path can process representative nominal-ADT cases too.
- Unsupported backends produce explicit errors rather than escaping into `object` fallback.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_*adt*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*adt*.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Implementation Order

1. Fix language surface and non-goals
2. Fix ADT / pattern / match schema
3. Add frontend/selfhost parser support
4. Add EAST2 -> EAST3 lowering and static checking
5. Implement a representative backend
6. Verify convergence of built-in and user-defined ADTs
7. Roll out to more backends / docs / archive

## Breakdown

- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] Inventory candidate language surfaces for nominal ADT declarations, constructors, variant access, and `match`, then decide on a selfhost-safe staged introduction path.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] Fix the boundary between type-system base work and full language-feature work so this plan does not overlap with `P1-EAST-TYPEEXPR-01`.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] Extend `spec-east` / `spec-user` / `spec-dev` with nominal-ADT declaration surface, pattern nodes, match nodes, and diagnostic contracts.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] Fix the static-check policy and error categories for exhaustiveness, duplicate patterns, and unreachable branches.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] Update frontend and selfhost parser paths so they can accept representative nominal-ADT syntax.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] Introduce ADT constructors, variant tests, variant projection, and `match` lowering into EAST/EAST3.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] Verify through representative tests that built-in `JsonValue` and user-defined nominal ADTs use the same IR category.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] Implement the minimal constructor / variant-check / destructuring / `match` path in a representative backend (first C++) and forbid silent fallback.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] Organize rollout order and fail-closed policy for other backends, and fix diagnostics for unsupported targets.
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] Refresh selfhost / docs / archive / migration notes and close the full nominal-ADT rollout plan.

### S5-01 Rollout Order And Fail-Closed Policy

- Fix the rollout order as:
  - Wave 1: `Rust` / `C#` / `Go` / `Java` / `Kotlin` / `Scala` / `Swift` / `Nim`
  - Wave 2: `JS` / `TS` on the shared JS emitter lane
  - Wave 3: `Lua` / `Ruby` / `PHP`
- The representative unsupported lane is split in two: the lane-level nominal ADT v1 guard for `Rust/C#`, and the `Match` statement carrying `NominalAdtMatch` for the remaining backends.
- Unsupported backends must fail closed. `Rust/C#` keep the `unsupported_syntax|... does not support nominal ADT v1 lanes yet` guard; the remaining targets use backend-local `unsupported stmt kind: Match` diagnostics.
- Comment-based or silent fallback is forbidden. This slice removes Nim's old `# unsupported stmt: Match` fallback.
- The non-C++ contract guard must pin the same fail-closed policy across Wave 1 / Wave 2 / Wave 3 representative targets.

## Implementer Notes

### Do not do first

- Canonicalize ad hoc syntax that only works for `JsonValue`
- Canonicalize an ADT surface that only works in C++
- Grow backend-local `match` special cases before exhaustiveness rules exist

### Decide first

- Constructor form
- Variant naming/namespace rules
- Whether `match` is an expression, a statement, or both
- Initial scope for wildcard / guards / nested patterns

### S1-01 Candidate Inventory

- Candidate A: reuse existing `class` + single inheritance + `@dataclass`, with a sealed base and top-level variant classes
  - Example: `@sealed class Result: ...`, `@dataclass class Ok(Result): value: T`, `@dataclass class Err(Result): error: E`
  - Pros: reuses the largest possible subset of syntax that the current parser/selfhost path already understands
  - Cons: namespace sugar such as `Result.Ok(...)` would need to come later
- Candidate B: nest variant classes under the base class
  - Example: `class Result: @dataclass class Ok(Result): ...`
  - Pros: better family grouping on the surface
  - Cons: larger impact on selfhost, symbol resolution, and backend naming
- Candidate C: introduce a dedicated `enum`-like or `adt` declaration block
  - Example: `adt Result: Ok(value: T); Err(error: E)`
  - Pros: makes ADT intent the clearest
  - Cons: too expensive for the first rollout because parser, selfhost, formatting, and diagnostics all grow at once
- Candidate D: introduce a new expression-first surface together with `match`
  - Example: `match expr { Ok(v) => ... }`
  - Pros: strongest end-user ADT ergonomics
  - Cons: not selfhost-safe for the first stage because statement/expr grammar and lowering grow simultaneously

### S1-01 Decision

- The canonical initial declaration surface will be Candidate A
  - declare the sealed family with the existing `class` surface
  - declare variants as top-level classes with single inheritance from the base nominal ADT
  - use the existing `@dataclass` surface for payload-carrying variants
- The canonical initial constructor surface will be ordinary class calls
  - Example: `Ok(value=1)` or positional constructor calls
  - `Result.Ok(...)`, factory DSLs, or macro-like sugar stay out of the first stage
- The canonical initial variant-access surface will be `isinstance` plus field access
  - Example: `if isinstance(x, Ok): return x.value`
  - Do not reintroduce general dynamic helpers that overlap with the `JsonValue.as_*` lane
- `match` remains part of the language goal, but it is staged statement-first and is not part of the initial surface
  - Stage A uses `isinstance` narrowing plus field access as the source-of-truth surface
  - Stage B introduces a Python-like `match/case` statement as the representative surface
  - Stage C can add `match` expressions, guard patterns, and nested patterns
- For variant namespacing, v1 fixes top-level variant names as canonical
  - namespace sugar such as `Result.Ok` and nested variant declarations are deferred to Stage C or later

### Selfhost-safe staged introduction path

1. Stage A: allow nominal ADT families to be declared and used with existing `class` / `@dataclass` / `isinstance` only
2. Stage B: add a `match/case` statement over the same variant-class family
3. Stage C: add `match` expressions, guards, nested patterns, and namespace sugar
4. Stage D: revisit concise sugar such as `adt` blocks or `Result.Ok` if still justified

### S1-01 completion memo

- The canonical surface before parser/selfhost expansion is limited to reused `class` / `@dataclass` syntax
- `match` stays in scope for the overall feature, but it is deferred as a statement-first later stage
- New-syntax-first options such as nested variants, `adt` blocks, or expression-first `match` are not chosen for the first rollout

### S1-02 Responsibility Boundary

- Owned by P1: type-system groundwork
  - `TypeExpr` schema
  - classification of `OptionalType`, `UnionType(union_mode=dynamic)`, and `NominalAdtType`
  - authority relationship between `type_expr` and the `resolved_type` mirror
  - the IR contract that treats `JsonValue` as a nominal closed ADT lane
- Owned by P1: narrowing groundwork
  - generic narrowing semantics for `isinstance`, decode helpers, and variant-test equivalents
  - narrowing / decode / type-predicate metadata in `EAST2 -> EAST3`
  - validator contracts around `semantic_tag`, nominal names, and fail-closed mismatch handling
- Owned by P5: full language feature
  - the nominal-ADT declaration surface
  - constructors / variant access / destructuring / patterns / `match`
  - user-facing diagnostics for exhaustiveness, duplicate patterns, and unreachable branches
  - ADT / pattern / `match` syntax accepted by the selfhost parser
  - the representative backend surface that runs user-defined nominal ADTs end to end

### S1-02 handoff rules

1. Any change to `TypeExpr` kinds, union lanes, nominal-ADT categories, or generic narrowing metadata belongs to P1-side type groundwork.
2. Any change to how users write code, what the parser accepts, or how constructors / patterns / `match` appear on the surface belongs to P5-side language rollout.
3. The Stage A `class` / `@dataclass` / `isinstance` bridge is allowed as part of the P5 representative surface, but P5 must not redefine the generic type-predicate semantics of `isinstance` itself.
4. The decode-first semantics of built-in `JsonValue.as_*` / `get_*` remain authoritative in the IR/narrowing contract fixed by P1; P5 only owns the step that aligns user-defined ADT syntax with the same IR category.
5. If a new source surface in P5 requires a new `TypeExpr` kind or a new generic narrowing lane, that foundation must be pushed back into follow-up type-groundwork instead of being absorbed by P5 alone.

### Representative scope example

- Built-in: `JsonValue`
- User-defined: one closed ADT with 2-3 variants
- Pattern set: variant match plus payload binding, without literal-heavy extensions

Decision log:
- 2026-03-09: Added this P5 in response to the user request to treat the full nominal-ADT language rollout as later work than the current type-system foundation.
- 2026-03-09: Fixed the scope of this P5 to user-defined ADT syntax, constructors, `match`, exhaustiveness checking, and multi-backend rollout, excluding the type-system base itself.
- 2026-03-09: Fixed the policy that built-in `JsonValue` and user-defined ADTs must not become separate feature families; they must converge to one IR/lowering/backend category.
- 2026-03-11: Closed `S1-01` by inventorying candidate language surfaces and fixing the initial rollout to existing `class` + single inheritance + `@dataclass` + `isinstance`.
- 2026-03-11: Fixed `match` as a language goal but deferred it from the selfhost-safe initial stage; statement-first `match/case` is now the Stage B target.
- 2026-03-11: Fixed `Result.Ok`-style namespace sugar and `adt` blocks as later-stage sugar rather than canonical v1 syntax.
- 2026-03-11: Closed `S1-02` by fixing `TypeExpr` schema, union lanes, nominal-ADT categories, and generic narrowing metadata as P1 responsibilities, while declaration/constructor/pattern/`match` surface and user-facing diagnostics remain P5 responsibilities.
- 2026-03-11: Fixed the rule that Stage A may reuse `class` / `@dataclass` / `isinstance` as a representative P5 bridge, but P5 does not redefine the generic `isinstance` semantics or the decode-first IR contract already fixed for `JsonValue` by P1.
- 2026-03-11: Closed `S2-01` by adding the Stage-A `@sealed` family / top-level variant / `isinstance` surface to `spec-user`, adding `ClassDef.meta.nominal_adt_v1` plus `Match` / `MatchCase` / `VariantPattern` / `PatternBind` / `PatternWildcard` schema to `spec-east`, and fixing fail-closed diagnostic rules for nominal ADT / `match` introduction in `spec-dev`.
- 2026-03-11: Closed `S2-02` by fixing the rule that `Match` over a closed nominal ADT family must be exhaustive, while duplicate patterns and unreachable branches fail closed with `semantic_conflict`, and by recording the coverage summary in `Match.meta.match_analysis_v1`.
- 2026-03-11: For `S3-01`, fixed the representative parser scope to selfhost acceptance of `@sealed` families, variants whose family is defined earlier in the same module, mandatory `@dataclass` on payload variants, and `ClassDef.meta.nominal_adt_v1` emission for those representative cases.
- 2026-03-11: For `S3-01`, deferred imported-family support and variants declared before their family; the canonical first parser milestone is same-module, family-first nominal ADT syntax.
- 2026-03-11: Closed `S3-01` with representative parser support for `@sealed` families, same-module family-first variants, mandatory `@dataclass` payload variants, `ClassDef.meta.nominal_adt_v1` emission, and fail-closed misuse diagnostics.
- 2026-03-11: In `S3-02`, fixed representative constructor / family-variant test metadata plus variant-typed field access as `Attribute` with `NominalAdtProjection` metadata, while leaving branch-local narrowing projection and `match` lowering to later slices.
- 2026-03-11: As the first slice of `S3-02`, lowering now consults the same-module nominal ADT family/variant declaration table, seeds user-defined variant constructor calls as `NominalAdtCtorCall`, and seeds `isinstance(..., Variant/Family)` checks with `nominal_adt_test_v1` and `narrowing_lane_v1.predicate_category=nominal_adt`.
- 2026-03-11: `S3-02` will not jump straight to variant projection and `match` lowering; the representative constructor and variant-test metadata lane is fixed first by tests, and the next stage can build on that.
- 2026-03-11: Closed `S3-02` by fixing representative nominal ADT `Match` lowering with `NominalAdtMatch` metadata, `VariantPattern` with `NominalAdtVariantPattern` metadata, and payload-bind metadata carrying field types.
- 2026-03-11: Closed `S4-01` by fixing a representative test where the built-in `JsonValue` decode lane `receiver_type.category` and the user-defined nominal ADT `Match` subject `subject_type.category` both use `nominal_adt`.
- 2026-03-11: Closed `S4-02` by fixing representative C++ backend coverage so constructor / projection / `isinstance` stay on the existing class lane, `NominalAdtMatch` lowers to `if / else if`, and plain `Match` fail-closes with `unsupported Match lane`.
- 2026-03-11: As the first `S5-01` slice, fixed the rollout order to `C++ -> Rust -> C# -> the rest`, and locked Rust/C# to fail closed with `unsupported_syntax` for representative nominal ADT v1 `ClassDef.meta.nominal_adt_v1`, `Match`, and `NominalAdtProjection` lanes.
- 2026-03-11: Closed `S5-01` by fixing the multi-backend rollout order as `Rust/C#/Go/Java/Kotlin/Scala/Swift/Nim`, then shared-JS `JS/TS`, then `Lua/Ruby/PHP`.
- 2026-03-11: Closed `S5-01` by fixing the unsupported-backend contract to fail close through the Rust/C# lane-level `unsupported_syntax` guard or, for the remaining targets, backend-local `unsupported stmt kind: Match` diagnostics, and by removing Nim's old `# unsupported stmt` comment fallback.
- 2026-03-11: Closed `S5-02` by syncing `spec-user`, the tutorial, the C++ support matrix, and selfhost support-block guards to the formal nominal ADT v1 surface, and by fixing the migration note so Stage A remains the canonical `@sealed` + variant + `isinstance` source surface while the representative `match` lane stays a Stage B contract.
