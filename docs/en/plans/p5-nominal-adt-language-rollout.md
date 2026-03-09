# P5: Full rollout of nominal ADTs as a language feature

Last updated: 2026-03-09

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

- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] Inventory candidate language surfaces for nominal ADT declarations, constructors, variant access, and `match`, then decide on a selfhost-safe staged introduction path.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] Fix the boundary between type-system base work and full language-feature work so this plan does not overlap with `P1-EAST-TYPEEXPR-01`.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] Extend `spec-east` / `spec-user` / `spec-dev` with nominal-ADT declaration surface, pattern nodes, match nodes, and diagnostic contracts.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] Fix the static-check policy and error categories for exhaustiveness, duplicate patterns, and unreachable branches.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] Update frontend and selfhost parser paths so they can accept representative nominal-ADT syntax.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] Introduce ADT constructors, variant tests, variant projection, and `match` lowering into EAST/EAST3.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] Verify through representative tests that built-in `JsonValue` and user-defined nominal ADTs use the same IR category.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] Implement the minimal constructor / variant-check / destructuring / `match` path in a representative backend (first C++) and forbid silent fallback.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] Organize rollout order and fail-closed policy for other backends, and fix diagnostics for unsupported targets.
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] Refresh selfhost / docs / archive / migration notes and close the full nominal-ADT rollout plan.

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

### Representative scope example

- Built-in: `JsonValue`
- User-defined: one closed ADT with 2-3 variants
- Pattern set: variant match plus payload binding, without literal-heavy extensions

Decision log:
- 2026-03-09: Added this P5 in response to the user request to treat the full nominal-ADT language rollout as later work than the current type-system foundation.
- 2026-03-09: Fixed the scope of this P5 to user-defined ADT syntax, constructors, `match`, exhaustiveness checking, and multi-backend rollout, excluding the type-system base itself.
- 2026-03-09: Fixed the policy that built-in `JsonValue` and user-defined ADTs must not become separate feature families; they must converge to one IR/lowering/backend category.
