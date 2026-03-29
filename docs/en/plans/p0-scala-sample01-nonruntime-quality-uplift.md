<a href="../../ja/plans/p0-scala-sample01-nonruntime-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Improve `sample/01` Scala Quality (Excluding Runtime Externalization)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- Compared with the C++ version, `sample/scala/01_mandelbrot.scala` still has non-runtime redundancies (`Any` degradation, excessive casts, overuse of boundary labels).
- Runtime externalization is handled by a separate task (`P0-RUNTIME-EXT-SCALA-LUA-01`), so this plan focuses only on generated-code quality itself.
- The goal is to first produce Scala output that is readable/traceable even before runtime separation, so later runtime-separation diffs do not destabilize quality.

Goal:
- Reduce non-runtime redundancy in `sample/scala/01` and secure readability/type clarity closer to the C++ version.
- Implement improvements as reusable general Scala-emitter rules, not sample-only hacks.

In scope:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- `src/hooks/code_emitter.py` (only where Scala common-rule usage is involved)
- `tools/check/check_py2scala_transpile.py`
- `sample/scala/01_mandelbrot.scala` (reflected via regeneration)

Out of scope:
- Runtime helper externalization (implemented in `P0-RUNTIME-EXT-SCALA-LUA-01`)
- Adding/removing Scala runtime APIs
- Simultaneous optimization of non-Scala backends

Acceptance criteria:
- In hot paths of `sample/scala/01_mandelbrot.scala`, `mutable.ArrayBuffer[Any]` is replaced by typed containers.
- Unnecessary `boundary.Label` is not emitted in simple while/for-like paths.
- Same-type conversion chains (for example, `__pytra_int(0L)`) are reduced, and type-known paths are emitted as direct expressions.
- `tools/check/check_py2scala_transpile.py` and sample parity (`01_mandelbrot`) pass with no regression.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs scala --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets scala 01_mandelbrot --ignore-unstable-stdout`

Breakdown:
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-01] Compare `sample/cpp/01` and `sample/scala/01`, and lock non-runtime quality gaps (type degradation/redundant casts/control structures) as concrete fragments.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-02] Explicitly define non-runtime task boundaries (improvements handled here vs delegated to runtime externalization).
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-01] Implement typed-container emission rules that prevent `Any` degradation in hot paths such as `pixels`.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-02] Implement a fastpath that omits `boundary` output in simple loops without break/continue.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-03] Implement emission rules that reduce identity casts (`__pytra_int(0L)`, etc.) in type-known paths.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-04] Implement return-representation optimization that reduces `ArrayBuffer[Any]` dependency in small-return-value paths such as `color_map`.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-01] Add regression tests (code fragments) and lock quality indicators for `sample/scala/01`.
- [x] [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-02] Run Scala transpile/smoke/parity and confirm no regression.

Decision log:
- 2026-03-02: Per user instruction, opened a P0 ticket for Scala quality improvements on `sample/01` independent of runtime externalization.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-01] In comparison with `sample/cpp/01`, fixed priority gaps as "typed-container shortage", "boundary overuse", and "remaining identity casts".
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S1-02] Delegated runtime implementation/placement to P0-RUNTIME-EXT-SCALA-LUA-01 and fixed this plan's scope to generated-body quality after `// 01:`.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-01] Introduced `bytearray/list[int] -> mutable.ArrayBuffer[Long]` and reduced `pixels` in `sample/01` from `Any` to typed containers.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-02] Added a fastpath that omits `boundary` generation in `ForCore/While` when loop bodies do not contain `break/continue`.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-03] Omitted identity casts for `int/float` type-known arguments and `StaticRange` start/stop/step, reducing redundant `__pytra_int(...)` in `sample/01`.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S2-04] Reduced `tuple[int,int,int]` into `mutable.ArrayBuffer[Long]`, shrinking `ArrayBuffer[Any]` dependency in the `color_map` return path.
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-01] Added quality-fragment checks for `sample/01` in `check_py2scala_transpile.py` (regression detection for `boundary`/identity cast reintroduction).
- 2026-03-02: [ID: P0-SCALA-S01-NONRUNTIME-QUALITY-01-S3-02] Ran `check_py2scala_transpile.py` (135 cases) and sample parity (`--targets scala 01_mandelbrot`) and confirmed no regression.

## S1 Implementation Results (2026-03-02)

### S1-01: Locking Quality Gaps in `sample/cpp/01` vs `sample/scala/01`

- Gap A: container type degradation
  - Scala: `color_map(...): mutable.ArrayBuffer[Any]` / `pixels: mutable.ArrayBuffer[Any]`
  - C++: `std::tuple<int64,int64,int64>` / `bytearray`
  - Impact: Pixel loops become `Any`-based, lowering type clarity and readability.
- Gap B: control-structure verbosity
  - Scala: Multiple layers of `boundary` + `Label` inserted for each `while`.
  - C++: `for/while` emitted as straightforward syntax.
  - Impact: Noise increases even in hot loops that do not use `break/continue`.
- Gap C: identity-cast / helper chains
  - Scala: `__pytra_int(0L)`, `y < __pytra_int(height)`, `__pytra_int(escape_count(...))`
  - C++: Direct expressions in known `int64` paths (`0`, `y < height`, `escape_count(...)`).
  - Impact: Same-type conversions lengthen expressions and raise review/trace costs.

### S1-02: Explicit Non-Runtime Task Boundaries

- Handled in this plan:
  - Function-body output after `// 01:` comments (`escape_count/color_map/render_mandelbrot/run_mandelbrot`).
  - Emitter rules for typed containers / casts / loop fastpaths.
- Not handled in this plan:
  - `def __pytra_*` runtime helper implementations themselves.
  - Runtime file placement/loading paths and runtime-bundling rules at parity execution.
  - These remain responsibilities of P0-RUNTIME-EXT-SCALA-LUA-01.
