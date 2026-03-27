# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

Last updated: 2026-03-26

## Task-operation rules

- Every task must have both an `ID` and a context file under `docs/ja/plans/*.md`.
- The task to start is fixed to the highest-priority unfinished `ID`, meaning the smallest `P<number>`, and within the same priority the first item from the top. Do not move to a lower-priority task unless explicitly overridden.
- If even one `P0` item remains unfinished, do not start `P1` or below.
- Progress notes and commit messages must always include the same `ID`.
- When a task is completed, change `[ ]` to `[x]`, add a completion note such as counts or results, and commit it.
- Completed tasks are moved periodically into `docs/ja/todo/archive/`.
- For emitter parity tests, completion means `emit + compile + run + matching stdout`, not merely successful emit. Placeholder code may still exist if only emit succeeds.

## Unfinished tasks

### P1-EMIT-GO-PARITY: Fix Go emitter compile + run parity

Context: [docs/ja/plans/p1-emit-go-parity.md](../plans/p1-emit-go-parity.md)
Required reading: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-GO-PARITY-S1] Implement Go lowering for list and dict comprehensions
2. [x] [ID: P1-GO-PARITY-S2] Fix missing EAST coverage: lower `write_text` and similar calls to `BuiltinCall` in resolve, add parser support for `with`, and propagate `bytearray` type information
3. [ ] [ID: P1-GO-PARITY-S3] Achieve `go run` + matching stdout on all 132 fixtures
4. [ ] [ID: P1-GO-PARITY-S4] Achieve `go run` + matching stdout on all 18 samples, including matching PNG/GIF artifact CRC32

### P1-SPEC-CONFORM2: Specification conformance phases 2 and 3, responding to additional Codex review findings

Context: [docs/ja/plans/p1-spec-conform2.md](../plans/p1-spec-conform2.md)

Phase 1, `link`, is complete. Phase 2, `emit`, and Phase 3, `optimize/compile`, remain.

Phase 2: `emit`, remove the workarounds

7. [ ] [ID: P1-SPEC-CONFORM2-S7] `emit/go/emitter.py`: remove type inference, type rewriting, extra casts, and hard-coded module checks
8. [ ] [ID: P1-SPEC-CONFORM2-S8] `emit/cpp/emitter.py`: same cleanup
9. [ ] [ID: P1-SPEC-CONFORM2-S9] `emit/common/code_emitter.py`: restructure so branching depends only on `mapping.json`

Phase 3: `optimize / compile`, move type responsibility back to earlier stages

10. [ ] [ID: P1-SPEC-CONFORM2-S10] `optimize/passes/typed_repeat_materialization.py`: remove backfilled `resolved_type` completion
11. [ ] [ID: P1-SPEC-CONFORM2-S11] `optimize/passes/typed_enumerate_normalization.py`: same cleanup
12. [ ] [ID: P1-SPEC-CONFORM2-S12] `compile/passes.py`: revert the early `int32` injection and stay aligned with current spec until P4-INT32 starts
13. [ ] [ID: P1-SPEC-CONFORM2-S13] Regenerate golden outputs and confirm parity remains intact

### P1-EMIT-CPP: C++ emitter

Working directory: `toolchain2/emit/cpp/`
Required reading: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-EMIT-CPP-S1] Implement a new C++ emitter under `toolchain2/emit/cpp/` and reach emit success: 132/132 fixtures and 18/18 samples emit successfully
2. [ ] [ID: P1-EMIT-CPP-S2] Adjust the existing `src/runtime/cpp/` to match the new pipeline emitter output. Do not create a new runtime. Keep using the current split layout such as `built_in/`, `std/`, and `core/`. Add `src/runtime/cpp/mapping.json`, and follow the naming rules in plan section 3.4. Do not `git push` until runtime behavior is confirmed.
3. [ ] [ID: P1-EMIT-CPP-S3] Make all 18 samples pass parity tests. Completion means `emit + g++ compile + run + matching stdout`. Emit-only success is not enough.
4. [x] [ID: P1-EMIT-CPP-S4] Switch `pytra-cli2 -emit --target=cpp` to the `toolchain2` emitter
5. [x] [ID: P1-EMIT-CPP-S5] Remove all dependency on `toolchain/` and delete `toolchain/`. `pytra-cli2.py` now has zero imports from it.

### P2-SELFHOST: Transpilation tests for toolchain2 itself

Context: `docs/ja/plans/plan-pipeline-redesign.md` section 3.5

1. [x] [ID: P2-SELFHOST-S1] Parse all `.py` files under `src/toolchain2/`: 37/46 succeeded. The remaining 9 use still-unsupported syntax such as recursive `ParseContext`, `Union` forward refs, and walrus
2. [x] [ID: P2-SELFHOST-S2] Run through `parse -> resolve -> compile -> optimize`: all 37 passed
3. [x] [ID: P2-SELFHOST-S3] Place golden outputs under `test/selfhost/` and keep them as regression tests: 37 cases each for `east1`, `east2`, `east3`, and `east3-opt`
4. [ ] [ID: P2-SELFHOST-S4] Transpile toolchain2 to Go with the Go emitter and make `go build` pass. Emit is 25/25, but `go build` still fails on docstring and syntax issues.

### P4: Change the default size of `int` from `int64` to `int32`

Pytra currently normalizes Python `int` to `int64`, but `int` is 32-bit in C++, Go, Java, and C#, and that is usually enough.
Using 64-bit values hurts memory and cache efficiency. The plan is to change the default from `int` to `int32`, while requiring users to write `int64` explicitly where 64-bit values are needed.

Affected areas:

- Change the normalization rule in `spec-east.md` section 6.2
- Regenerate all golden outputs
- Update type mappings in all emitters
- Check all samples for overflow, including intermediate values that may exceed 32 bits
- Change the return type of `len()` to `int32`

Prerequisite: Start only after Go selfhost is complete.

1. [ ] [ID: P4-INT32-S1] Change the normalization rule in `spec-east.md` / `spec-east2.md` from `int` to `int32`
2. [ ] [ID: P4-INT32-S2] Fix type normalization in resolve
3. [ ] [ID: P4-INT32-S3] Check all 18 samples for overflow and mark required locations explicitly as `int64`
4. [ ] [ID: P4-INT32-S4] Regenerate golden outputs and confirm parity across all emitters

Note: Completed tasks have already been moved to [the archive](archive/index.md).
