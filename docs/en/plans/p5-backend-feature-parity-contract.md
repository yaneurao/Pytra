# P5 Backend Feature Parity Contract

Last updated: 2026-03-12

Purpose:
- Stop treating C++ as the de facto feature-spec implementation and instead fix a cross-backend feature contract for syntax, builtins, and `pytra.std.*`.
- Ensure unsupported backend lanes fail closed instead of degrading via silent fallback or ad-hoc behavior.
- Create the feature inventory that later conformance suites, support matrices, and rollout policy will depend on.

Background:
- Pytra currently tends to advance through a representative C++ lane first, which makes feature handling uneven across Rust, C#, and other backends.
- `py_runtime.h` shrink work is more urgent in the short term, but backend parity still needs a fixed policy afterward rather than another round of “catch up later.”
- If parity remains a follow-up task only, C++-only implementations and object/String fallback behavior will drift back in.
- Fixing feature IDs, support states, and fail-closed rules first lets the project tolerate backend progress differences without losing the specification baseline.

Out of scope:
- Immediately implementing every feature in every backend.
- A full rewrite of `pytra.std.*`.
- Immediate `py_runtime.h` shrink work.
- Final cleanup of every backend runtime implementation detail.

Acceptance criteria:
- There is a defined plan for inventorying syntax, builtins, and `pytra.std.*` by feature ID.
- Backend support-state categories such as `supported`, `fail_closed`, `not_started`, and `experimental` are fixed.
- Unsupported backends are explicitly required to stop with `unsupported_syntax` / `not_implemented` style diagnostics instead of silently degrading.
- New-feature acceptance rules are defined so “C++ works” does not mean “feature complete.”
- The `docs/en/` mirror matches the Japanese source plan.

## Child tasks

- [x] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-01] Inventory representative syntax / builtin / `pytra.std.*` features by feature ID and fix the category and naming rules.
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S1-02] Fix backend support-state categories (`supported` / `fail_closed` / `not_started` / `experimental`) and the conditions for each.
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-01] Define fail-closed policy and diagnostic categories for unsupported backend lanes and forbid silent fallback.
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S2-02] Define the acceptance rule for new features so the project does not treat “works in C++ only” as completion.
- [ ] [ID: P5-BACKEND-FEATURE-PARITY-CONTRACT-01-S3-01] Prepare the representative inventory document/tooling handoff so later conformance-suite and support-matrix work can attach cleanly.

## S1-01 Representative Inventory

- source of truth: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py)
- validation: [check_backend_feature_contract_inventory.py](/workspace/Pytra/tools/check_backend_feature_contract_inventory.py), [test_check_backend_feature_contract_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_backend_feature_contract_inventory.py)
- category rule:
  - `syntax`: `syntax.<area>.<feature>`
  - `builtin`: `builtin.<domain>.<feature>`
  - `stdlib`: `stdlib.<module>.<feature>`
- The representative inventory is not an exhaustive catalog; it is the fixed representative feature set that later conformance and support-matrix work will attach to.
- `syntax` representative:
  - `syntax.assign.tuple_destructure`
  - `syntax.expr.lambda`
  - `syntax.expr.list_comprehension`
  - `syntax.control.for_range`
  - `syntax.control.try_raise`
  - `syntax.oop.virtual_dispatch`
- `builtin` representative:
  - `builtin.iter.range`
  - `builtin.iter.enumerate`
  - `builtin.iter.zip`
  - `builtin.type.isinstance`
  - `builtin.bit.invert_and_mask`
- `stdlib` representative:
  - `stdlib.json.loads_dumps`
  - `stdlib.pathlib.path_ops`
  - `stdlib.enum.enum_and_intflag`
  - `stdlib.argparse.parse_args`
  - `stdlib.math.imported_symbols`
  - `stdlib.re.sub`

## Decision log

- 2026-03-12: Backend parity matters, but it should not block the near-term `P0-P4` `py_runtime.h` shrink work, so it is tracked as `P5`.
- 2026-03-12: The parity source of truth is the feature contract / EAST3 contract / `pytra.std.*` contract, not the C++ implementation.
- 2026-03-12: `S1-01` fixes the representative inventory source of truth in [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py) and freezes the category set at `syntax` / `builtin` / `stdlib`.
