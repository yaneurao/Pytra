# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation mirror.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-01

## Context Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- Priority overrides must be instructed in chat using `docs/ja/plans/instruction-template.md` format; do not use `todo2.md`.
- Default execution target is the highest-priority unfinished ID (smallest `P<number>`, first in order within same priority). Do not move to lower priority without explicit override.
- If any `P0` is unfinished, do not start `P1` or below.
- Before starting, confirm `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress notes and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memo in `docs/ja/todo/index.md` to one line; detailed judgment/verification logs belong in the context file (`docs/ja/plans/*.md`) `Decision log`.
- If one `ID` is large, split into child tasks (`-S1` / `-S2`, etc.) in the context file while keeping parent checkbox open until parent is done.
- If uncommitted changes remain due to interruption, do not start another `ID` until completing the same `ID` or reverting diffs.
- When updating `docs/ja/todo/index.md` / `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and confirm new progress `ID` matches top unfinished `ID` (or its child).
- Append work-time decisions to the context file `Decision log`.
- For temporary outputs, use existing `out/` (or `/tmp` only when needed); do not keep creating new top-level temporary folders in the repository.

## Notes

- This file stores unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` is index-only; history bodies are saved by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P0: Improve non-C++ inheritance method dynamic dispatch (all backends)

Context: [docs/ja/plans/p0-multilang-inheritance-dispatch-rollout.md](../plans/p0-multilang-inheritance-dispatch-rollout.md)

1. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01] Align inheritance method dynamic dispatch and `super()` behavior to Python compatibility across non-C++ backends.
2. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JAVA] Execute the Java uplift plan [p0-java-inheritance-dispatch-uplift.md](../plans/p0-java-inheritance-dispatch-uplift.md).
3. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-JS] Execute the JS uplift plan [p0-js-inheritance-dispatch-uplift.md](../plans/p0-js-inheritance-dispatch-uplift.md).
4. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-TS] Execute the TS uplift plan [p0-ts-inheritance-dispatch-uplift.md](../plans/p0-ts-inheritance-dispatch-uplift.md).
5. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-KOTLIN] Execute the Kotlin uplift plan [p0-kotlin-inheritance-dispatch-uplift.md](../plans/p0-kotlin-inheritance-dispatch-uplift.md).
6. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-SWIFT] Execute the Swift uplift plan [p0-swift-inheritance-dispatch-uplift.md](../plans/p0-swift-inheritance-dispatch-uplift.md).
7. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RS] Execute the Rust uplift plan [p0-rs-inheritance-dispatch-uplift.md](../plans/p0-rs-inheritance-dispatch-uplift.md).
8. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY] Execute the Ruby uplift plan [p0-ruby-inheritance-dispatch-uplift.md](../plans/p0-ruby-inheritance-dispatch-uplift.md).
9. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA] Execute the Lua uplift plan [p0-lua-inheritance-dispatch-uplift.md](../plans/p0-lua-inheritance-dispatch-uplift.md).
10. [ ] [ID: P0-MULTILANG-INHERIT-DISPATCH-01-S3-01] Aggregate parity/smoke results across all backends and separate unresolved blockers.

### P1: Improve `sample/go/01` output quality (reduce gap vs C++)

Context: [docs/ja/plans/p1-go-sample01-quality-uplift.md](../plans/p1-go-sample01-quality-uplift.md)

1. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01] Improve `sample/01` output quality in Go backend and reduce the gap vs C++ output.
2. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/go/01` (redundant casts / loop shape / no-op / `any` fallback) and lock implementation priority.
3. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Go emitter numeric output and prioritize typed paths.
4. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers `range(stop)` / `range(start, stop, 1)` into canonical `for`.
5. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] Route `write_rgb_png` from no-op to native runtime call and fail closed when unresolved.
6. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] Add typed container fastpath to suppress `[]any` fallback in `sample/01` `pixels` hot path.
7. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock `sample/go/01` regenerated diff.

### P1: Improve `sample/kotlin/01` output quality (reduce gap vs C++)

Context: [docs/ja/plans/p1-kotlin-sample01-quality-uplift.md](../plans/p1-kotlin-sample01-quality-uplift.md)

1. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01] Improve `sample/01` output quality in Kotlin backend and reduce the gap vs C++ output.
2. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/kotlin/01` (redundant casts / loop shape / no-op / `Any?` fallback) and lock implementation priority.
3. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Kotlin emitter numeric output and prioritize typed paths.
4. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
5. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] Route `write_rgb_png` from no-op to native runtime call and fail closed when unresolved.
6. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] Add typed container fastpath in `sample/01` `pixels` path to suppress `MutableList<Any?>` fallback.
7. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock `sample/kotlin/01` regenerated diff.

### P1: Improve `sample/swift/01` output quality (reduce gap vs C++)

Context: [docs/ja/plans/p1-swift-sample01-quality-uplift.md](../plans/p1-swift-sample01-quality-uplift.md)

1. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01] Improve `sample/01` output quality in Swift backend and reduce the gap vs C++ output.
2. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/swift/01` (redundant casts / loop shape / no-op / `[Any]` fallback) and lock implementation priority.
3. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Swift emitter numeric output and prioritize typed paths.
4. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
5. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] Route `write_rgb_png` from no-op to native runtime call and fail closed when unresolved.
6. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] Add typed container fastpath in `sample/01` `pixels` path to suppress `[Any]` fallback.
7. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock `sample/swift/01` regenerated diff.

### P1: Improve `sample/ruby/01` output quality (reduce gap vs C++)

Context: [docs/ja/plans/p1-ruby-sample01-quality-uplift.md](../plans/p1-ruby-sample01-quality-uplift.md)

1. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01] Improve `sample/01` output quality in Ruby backend and reduce the gap vs C++ output.
2. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] Inventory quality gaps in `sample/ruby/01` (redundant casts / loop / truthy path / temporary initialization) and lock implementation priority.
3. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Reduce same-type conversion chains in Ruby emitter numeric output and prioritize typed paths.
4. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] Add fastpath that lowers simple `range` loops into canonical loops.
5. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] Optimize insertion conditions for `__pytra_truthy` in comparisons/logical expressions and prioritize native Ruby conditions.
6. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] Add typed-assignment fastpath to remove unnecessary `nil` initialization for `r/g/b` and similar locals in `sample/01`.
7. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments + parity) and lock `sample/ruby/01` regenerated diff.

### P1: Improve `sample/lua/01` output quality (readability and redundancy reduction)

Context: [docs/ja/plans/p1-lua-sample01-quality-uplift.md](../plans/p1-lua-sample01-quality-uplift.md)

1. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01] Improve readability/redundancy of `sample/lua/01` and reduce the gap vs C++ output.
2. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] Lock redundant points in `sample/lua/01` (implicit runtime dependency / nil initialization / loop shape) with code fragments.
3. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] Make runtime-dependent outputs explicit (`int/float/bytearray` etc.) to improve self-contained output quality.
4. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] Remove unnecessary `nil` initialization for `r/g/b` on typed paths.
5. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] Add fastpath that simplifies step/parenthesis output for simple `range` loops.
6. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] Add regression tests and lock `sample/lua/01` regenerated diff.

### P1: Improve `sample/rs/08` output quality (readability + hot-path slimming)

Context: [docs/ja/plans/p1-rs-s08-quality-uplift.md](../plans/p1-rs-s08-quality-uplift.md)

1. [ ] [ID: P1-RS-S08-QUALITY-01] Improve generation quality of `sample/rs/08` and raise readability/hot-path efficiency.
2. [ ] [ID: P1-RS-S08-QUALITY-01-S1-01] Lock redundant points in `sample/rs/08` (clone/index normalization/loop/branch/capture condition/capacity) with code fragments.
3. [ ] [ID: P1-RS-S08-QUALITY-01-S2-01] Introduce emission rule that removes unnecessary `clone` on `capture` return path.
4. [ ] [ID: P1-RS-S08-QUALITY-01-S2-02] Add fastpath that omits index-normalization expressions where non-negative indexes are guaranteed.
5. [ ] [ID: P1-RS-S08-QUALITY-01-S2-03] Add fastpath that lowers simple range-derived loops to Rust `for`.
6. [ ] [ID: P1-RS-S08-QUALITY-01-S2-04] Add emission rule that simplifies `if/elif` chains into `else if` / `match` equivalents.
7. [ ] [ID: P1-RS-S08-QUALITY-01-S2-05] Add fastpath replacing `%`-based capture condition with a next-capture counter.
8. [ ] [ID: P1-RS-S08-QUALITY-01-S2-06] Add `reserve` emission rule for `frames` when size can be estimated.
9. [ ] [ID: P1-RS-S08-QUALITY-01-S3-01] Add regression tests and lock `sample/rs/08` regenerated diff.
10. [ ] [ID: P1-RS-S08-QUALITY-01-S3-02] Run transpile/smoke/parity and confirm non-regression.

### P3: Roll out container reference-management model to non-C++ backends

Context: [docs/ja/plans/p3-multilang-container-ref-model-rollout.md](../plans/p3-multilang-container-ref-model-rollout.md)

1. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01] Roll out the common policy to non-C++ backends: "dynamic boundaries use reference management, while type-known non-escape paths stay value-typed."
2. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] Inventory current container ownership model per backend (value/reference/GC/ARC) and build a gap matrix.
3. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] Specify common terms and rules for "reference-management boundary", "typed/non-escape reduction", and "escape conditions".
4. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] Design minimal EAST3 extension to retain/propagate container ownership hints in node metadata.
5. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] Define backend-neutral ownership decision API used by the `CodeEmitter` base.
6. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Implement pilot in Rust backend and add split between `object` boundary and typed value path.
7. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] Implement pilot in a GC backend (Java or Kotlin) and validate reduction under the same rule set.
8. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] Add regression tests for two pilot backends (unit + sample fragments) and lock recurrence detection.
9. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] Roll out sequentially to `cs/js/ts/go/swift/ruby/lua` and absorb backend-specific differences.
10. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] Run parity/smoke checks to confirm non-regression; record unresolved items separately as blockers.
11. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] Add operation rules (reference-management boundary / rollback) to `docs/ja/how-to-use.md` and backend specs.

### P3: Isolate C# selfhost-originated fixes from `CodeEmitter`

Context: [docs/ja/plans/p3-codeemitter-cs-isolation.md](../plans/p3-codeemitter-cs-isolation.md)

1. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01] Isolate C# selfhost-originated fixes from `CodeEmitter` and restore common-layer responsibilities to backend-neutral form.
2. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] Inventory `CodeEmitter` diffs since `v0.4.0` and classify into three groups: "common-required / C#-specific / pending judgment".
3. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] Document the judgment criteria for "common-required" (backend neutrality / usage in other languages / fail-closed necessity).
4. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] Move "C#-specific" changes into `CSharpEmitter` / C# runtime / selfhost-preparation layers.
5. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] Remove C#-specific workaround code from `CodeEmitter` and restore common implementation.
6. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] Run unit/selfhost regressions and confirm C# pass is maintained with no regression in other backends.

### P4: Full multi-language selfhost completion (Very low)

Context: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] Gradually establish selfhost for `cpp/rs/cs/js/ts/go/java/swift/kotlin` and make full multistage monitoring passable across all languages.
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] Resolve JS selfhost stage2 dependency-transpile failure and pass multistage.
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] Resolve TypeScript preview-only status and move to a selfhost-executable generation mode.
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Link with Go/Java/Swift/Kotlin native-backend tasks and enable selfhost execution chain.
5. [ ] [ID: P4-MULTILANG-SH-01-S4-01] Integrate all-language multistage regressions into CI path to continuously detect failure-category recurrence.
6. [ ] [ID: P4-MULTILANG-SH-01-S4-02] Document completion-judgment template (stage-pass and exclusion conditions per language) and lock operation rules.
- Completed child tasks (`S1-01` to `S2-02-S3`) and past progress notes were moved to `docs/ja/todo/archive/20260301.md`.
