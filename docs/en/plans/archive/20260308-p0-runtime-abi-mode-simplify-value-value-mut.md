<a href="../../../ja/plans/archive/20260308-p0-runtime-abi-mode-simplify-value-value-mut.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Simplify `@abi` Modes to `value` / `value_mut`

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01` in `docs/en/todo/archive/20260308.md`.

Background:
- The first `@abi` rollout used `default`, `value`, and `value_readonly`.
- In practice, most helper authors wanted the common case to read simply as “value,” while the mutable case should stand out.
- For C++, the practical interpretation was already:
  - `value` return values are value ABI,
  - read-only value arguments are the common case,
  - writable value arguments are special.

Objective:
- Make `value` the canonical read-only value ABI for arguments.
- Introduce `value_mut` for writable value arguments.
- Accept `value_readonly` only as a legacy source alias and normalize canonical metadata to `value`.

Acceptance criteria:
- public mode names become `default`, `value`, and `value_mut`
- argument-side `value` means read-only value ABI
- `value_readonly` is accepted only as a legacy alias
- `ret="value_mut"` is rejected
- docs, metadata, diagnostics, and representative helper usage are all synchronized

## Phases

### Phase 1: Contract

- inventory the old `default/value/value_readonly` contract
- fix the migration rule: `value` absorbs the old read-only mode and `value_mut` becomes the explicit mutable mode

### Phase 2: Parser and metadata

- update parser/decorator metadata/validator support
- update diagnostics and target-support checks

### Phase 3: Migration

- move representative helpers to the new names
- verify C++ helper/codegen regressions

### Phase 4: Closure

- update docs/how-to-use
- archive the completed plan

## Task Breakdown

- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-01] Inventory the old contract and fix the migration direction.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S1-02] Document canonical naming and migration rules.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-01] Update parser, metadata, and validator support.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-02] Update diagnostics and target checks.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-01] Migrate representative helpers such as `py_join`.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-02] Update regressions and confirm C++ non-regression.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-01] Synchronize docs and how-to-use.
- [x] [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S4-02] Archive the completed plan.

## Decision Log

- 2026-03-08: The public naming was simplified so the common read-only mode is simply `value`, while the rare mutable case becomes `value_mut`.
- 2026-03-08 [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-01]: Parser and metadata logic were updated so `value_readonly` is still accepted at source level as a compatibility alias, but canonical `runtime_abi_v1` metadata always normalizes it to `value`.
- 2026-03-08 [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S2-02]: `ret="value_mut"` was explicitly rejected to keep return-value ABI simple and fail-closed.
- 2026-03-08 [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-01]: Representative helpers such as `py_join` were moved to canonical `@abi(args={"parts": "value"}, ret="value")`.
- 2026-03-08 [ID: P0-RUNTIME-ABI-MODE-SIMPLIFY-01-S3-02]: EAST, linked-program, and C++ helper/codegen regressions were updated so the new naming is fixed end to end.
