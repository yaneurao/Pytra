<a href="../../ja/plans/p0-scala-sample01-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Improve `sample/scala/01` Quality (Reduce Gap vs C++ Quality)

Last updated: 2026-03-02

Related TODO:
- `ID: P0-SCALA-SAMPLE01-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- Compared with C++ output for the same case, `sample/scala/01_mandelbrot.scala` has a large gap in readability and type specialization.
- Main differences are:
  - Large runtime/helper embedding into a single generated file, reducing visibility of core code.
  - Frequent `Any` / `mutable.ArrayBuffer[Any]` degradation and chained `__pytra_*` conversions, making even type-known paths verbose.
  - Generic step-branch loops are emitted even for simple `range`, without reduction to canonical loops.
  - Re-wrapping with `__pytra_as_list` remains in the hot path for `pixels` appends.

Goal:
- Improve generated quality of `sample/scala/01` and move it toward a readable typed/native form closer to C++ output.

In scope:
- `src/hooks/scala/emitter/scala_native_emitter.py`
- (if needed) Scala runtime-helper emission strategy
- `test/unit/test_py2scala_smoke.py`
- Regeneration of `sample/scala/01_mandelbrot.scala`

Out of scope:
- Full optimization for all Scala backend cases
- Broadening coverage of Scala language features
- Simultaneous tuning for C++/Go/Rust backends

Acceptance criteria:
- In `sample/scala/01_mandelbrot.scala`, same-type chains like `__pytra_float(__pytra_float(...))` / `__pytra_int(__pytra_int(...))` are eliminated.
- `step==1` loops originating from `for i in range(...)` reduce to canonical loops.
- Re-wrapping `__pytra_as_list(pixels)` is reduced in the `pixels` append hot path.
- Runtime/helper embedding strategy is fixed, and visibility improvement is confirmed at least in `sample/01`.
- `test_py2scala_smoke` and Scala sample parity (at minimum `01_mandelbrot`) pass with no regression.

Verification commands (planned):
- `python3 tools/regenerate_samples.py --langs scala --force`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala 01_mandelbrot`

Breakdown:
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-01] Compare `sample/scala/01` and `sample/cpp/01`, and lock redundant items (cast/loop/runtime embedding/typed degradation) as concrete fragments.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-02] Finalize Scala-emitter improvement priority order (readability impact x implementation difficulty).
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-01] Reduce same-type cast chains in numeric-expression emission and prioritize typed paths.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-02] Add fastpaths lowering `range(stop)` / `range(start, stop, 1)` to canonical loops.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-03] Prioritize typed path usage for `mutable.ArrayBuffer[Any]` in `pixels` append hot paths and reduce re-wrapping.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-04] Implement reduction strategy for runtime/helper embedding (externalize or minimal embed) and improve `sample/01` readability.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-01] Add regression tests (code fragments) and lock diffs for `sample/scala/01`.
- [x] [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-02] Regenerate `sample/scala` and run smoke/parity to confirm no regression.

S1 Inventory (2026-03-02):
- Size gap: `sample/scala/01_mandelbrot.scala` is 706 lines, while `sample/cpp/01_mandelbrot.cpp` is 91 lines; the main cause is single-file runtime/helper embedding.
- Cast chains (same type):
```scala
var __hoisted_cast_3: Double = __pytra_float(__pytra_float(max_iter))
r = __pytra_int(__pytra_int((__pytra_float(255.0) * __pytra_float((__pytra_float(t) * __pytra_float(t))))))
```
- Loop degradation (generic step branch):
```scala
val __step_2 = __pytra_int(1L)
while ((__step_2 >= 0L && y < __pytra_int(height)) || (__step_2 < 0L && y > __pytra_int(height))) {
```
- Append hot-path re-wrapping:
```scala
pixels = __pytra_as_list(pixels); pixels.append(r)
pixels = __pytra_as_list(pixels); pixels.append(g)
pixels = __pytra_as_list(pixels); pixels.append(b)
```

S1 priority (readability impact x implementation difficulty):
1. `S2-01` reduce same-type cast chains (high impact / low-to-medium difficulty)
2. `S2-03` append hot-path typed fastpath (high impact / medium difficulty)
3. `S2-02` canonical loop fastpath (medium impact / medium difficulty)
4. `S2-04` runtime/helper reduction (high impact / high difficulty)

Decision log:
- 2026-03-02: Per user instruction, planned quality uplift for `sample/scala/01` as P0 and fixed policy to register detailed TODO breakdown.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-01] Compared `sample/scala/01` and `sample/cpp/01` and fixed redundant fragments (cast chains / generic-step loops / append re-wrapping / runtime embedding).
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S1-02] Finalized implementation priority as `cast -> append -> loop -> runtime reduction`.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-01] Added same-type wrapper normalization (`_to_*`) and type-known operand fastpaths to `scala_native_emitter`, removing `__pytra_float(__pytra_float(` / `__pytra_int(__pytra_int(` from `sample/scala/01`.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-02] Added canonical-while fastpath (`while (i < stop)`) for `step==1` in `ForCore(StaticRangeForPlan)`, reducing `__step` branch loops.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-03] Added a fastpath in append statements: when a typed local (`mutable.ArrayBuffer[Any]`) is detected, emit direct `pixels.append(...)` without `__pytra_as_list` re-wrap.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-01] Added `test_sample_01_quality_fastpaths_reduce_redundant_wrappers` to `test_py2scala_smoke.py` and locked cast/loop/append fragments as regressions.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S3-02] Regenerated all `sample/py/*.py -> sample/scala/*.scala`; confirmed `test_py2scala_smoke` (17 tests) and `runtime_parity_check --all-samples --targets scala` (18/18 pass). `tools/regenerate_samples.py --langs scala` is not yet supported (`unknown language(s): scala`), so this remains tracked in another P0.
- 2026-03-02: [ID: P0-SCALA-SAMPLE01-QUALITY-01-S2-04] Switched runtime helper handling from "embed everything" to "embed only helpers actually referenced by generated code via dependency closure." `sample/scala/01` shrank from 703 lines to 310 lines, and unused helpers such as `__pytra_save_gif` were removed. Smoke (17) and parity (18) both passed.
