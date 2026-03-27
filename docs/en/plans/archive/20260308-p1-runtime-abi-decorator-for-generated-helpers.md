<a href="../../../ja/plans/archive/20260308-p1-runtime-abi-decorator-for-generated-helpers.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Introduce an `@abi` Decorator for Generated / Runtime Helpers

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P1-RUNTIME-ABI-DECORATOR-01` in `docs/en/todo/archive/20260308.md`.

Background:
- Some runtime helpers are written in pure Python but need a fixed boundary ABI when emitted for C++, especially before runtime helpers are fully integrated into the linked-program path.
- `@extern` already means “the implementation lives elsewhere,” but it does not describe a generated helper whose implementation still comes from Python while its boundary ABI must be fixed.

Objective:
- Introduce `@abi` as a boundary-policy decorator independent from `@extern`.
- Allow generated/runtime helpers to declare fixed helper ABI at the function boundary.
- Keep validation strict enough to reject mutation of read-only value arguments and reject unsupported targets.

Acceptance criteria:
- `@abi` is specified as a first-class contract in `spec-abi`
- EAST / linked metadata carry `runtime_abi_v1`
- C++ gets a minimal lowering path for representative helpers
- representative helpers such as `py_join` use `@abi`
- unsupported targets fail closed

## Task Breakdown

- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-01] Specify syntax, semantics, modes, and separation from `@extern`.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-02] Fix EAST / linked metadata format.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-01] Add the decorator to the standard surface and preserve it through parsing / AST build.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-02] Add mutation checks for read-only value arguments.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-01] Implement minimal C++ lowering for `@abi(args, ret)`.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-02] Migrate representative helpers such as `py_join`.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-01] Add unit tests for coexistence, unsupported targets, and invalid mutation.
- [x] [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-02] Sync docs and record the dependency release for later plans.

## Decision Log

- 2026-03-08 [ID: P1-RUNTIME-ABI-DECORATOR-01-S1-01]: `@abi` was fixed as a boundary-policy decorator, distinct from `@extern`, which remains the implementation-location marker.
- 2026-03-08 [ID: P1-RUNTIME-ABI-DECORATOR-01-S2-02]: Validation was added so read-only value arguments cannot be mutated and unsupported backends reject `@abi` fail-closed.
- 2026-03-08 [ID: P1-RUNTIME-ABI-DECORATOR-01-S3-02]: `py_join` was moved to `@abi(args={"parts": "value_readonly"}, ret="value")` during the first rollout, allowing generated C++ runtime helpers to avoid exposing `rc<list<str>>` directly.
- 2026-03-08 [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-01]: Tests fixed coexistence with `@extern`, C++ lowering behavior, and rejection on unsupported targets.
- 2026-03-08 [ID: P1-RUNTIME-ABI-DECORATOR-01-S4-02]: The result was recorded as sufficient for later `py_runtime` slimming work, meaning `str.join` was no longer a blocker.
