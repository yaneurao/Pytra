# P0: Improve Output Quality for sample/cpp/08 (readability + hot-path reduction)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-CPP-S08-QUALITY-01` in `docs/en/todo/index.md`

Background:
- `sample/cpp/08_langtons_ant.cpp` works, but generated-code quality still has room for improvement.
- Specifically:
  - `grid` initialization is verbose with IIFE + `py_repeat`.
  - `capture` performs `bytes(frame)` conversion, leaving an unnecessary expression under `bytes` alias (`bytearray`) assumptions.
  - `%` is used heavily in a 600k-step hot loop.
  - Branches originating from `elif` become deeply nested `if` blocks.
  - `frames` has no `reserve`, so reallocation cost is unpredictable.

Goal:
- Improve generated code for `sample/cpp/08` in both readability and hot-path efficiency while preserving semantics.

Scope:
- `src/hooks/cpp/emitter/*` (around stmt/expr/forcore/call)
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (when needed)
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/08_langtons_ant.cpp` (verify after regeneration)

Out of scope:
- Algorithm changes to `sample/08`
- Breaking runtime ABI changes
- Bulk optimization across all samples other than `sample/08`

Acceptance criteria:
- In `sample/cpp/08_langtons_ant.cpp`, the following five points are confirmed.
  1. `grid` initialization is reduced from IIFE + `py_repeat` to concise typed initialization.
  2. Unnecessary `bytes(frame)` expression is reduced in `capture` return generation.
  3. Heavy `%` use in hot loops is reduced (at least capture-condition `%` replaced with counter style).
  4. Direction branches are simplified from nested `if` chains to `else if`/`switch` equivalent.
  5. Pre-`reserve` is added for `frames` to reduce reallocations.
- `check_py2cpp_transpile` and related unit tests pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/08_langtons_ant.py -o sample/cpp/08_langtons_ant.cpp`

Breakdown:
- [x] [ID: P0-CPP-S08-QUALITY-01-S1-01] Pin quality diffs in `sample/cpp/08` (initialization/conversion/branching/loop/capacity) as code fragments.
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-01] Reduce `grid` initialization from IIFE + `py_repeat` to typed direct initialization.
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-02] Simplify `bytes(frame)` on `capture` return by unnecessary-conversion reduction rules.
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-03] Introduce fast path replacing capture-condition `%` with next-capture counter style.
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-04] Reduce nested branching from `if/elif/elif/else` origin to `else if`/`switch` equivalent output.
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-05] Add minimal rules to emit `reserve` for pre-estimable `list`, and apply to `frames`.
- [x] [ID: P0-CPP-S08-QUALITY-01-S3-01] Add regression tests and pin regeneration diff for `sample/cpp/08`.
- [x] [ID: P0-CPP-S08-QUALITY-01-S3-02] Run transpile / unit / sample regeneration checks and verify non-regression.

Decision log:
- 2026-03-01: By user instruction, confirmed policy to break improvement points for `sample/cpp/08` into a P0 plan and add to TODO.
- 2026-03-01: Fixed quality diffs as S1-01 in `sample/cpp/08_langtons_ant.cpp`. Main fragments: `grid` initialization as `list<list<int64>> grid = [&]() -> ... py_repeat(...)` (verbose), `capture` as `return bytes(frame);` (unnecessary conversion), direction branch as `else { if (...) { ... } else { if (...) ... } }` (nested), and `frames` as `list<bytes> frames = list<bytes>{};` (no reserve).
- 2026-03-01: As S2-02, added reduction for known `bytes/bytearray` paths in `bytes_ctor` inside `src/hooks/cpp/emitter/runtime_expr.py`, simplifying `bytes(x)` to `x`.
- 2026-03-01: As S2-04, improved If emission in `src/hooks/cpp/emitter/stmt.py`, flattening `else: if ...` chains to `else if (...)`.
- 2026-03-01: As S2-01, added typed fill-constructor fast path for `[[seed] * cols for _ in range(rows)]` in `src/hooks/cpp/emitter/collection_expr.py`, reducing `grid` initialization in `sample/cpp/08` to `list<list<int64>>(h, list<int64>(w, 0))` (also applied to same-type initialization in sample13).
- 2026-03-01: As S2-03, in `ForCore(StaticRangeForPlan)` of `src/hooks/cpp/emitter/stmt.py`, detected trailing `if i % k == 0` guard and added fast path replacement to `if (i == __next_capture_*)` using `int64 __next_capture_*`.
- 2026-03-01: As S2-05, added rules on the same fast path to pre-emit `frames.reserve((steps_total + capture_every - 1) / capture_every);`.
- 2026-03-01: As S3-01, added two sample08 regressions to `test/unit/test_py2cpp_codegen_issues.py` (`else if` chain, `return frame;`).
- 2026-03-01: Extended S3-01 regressions and added unit checks that pin sample08 output for `grid` typed fill ctor / capture counter / reserve.
- 2026-03-01: As S3-02, verified `python3 src/py2cpp.py sample/py/08_langtons_ant.py -o sample/cpp/08_langtons_ant.cpp`, `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` (94 tests, OK), and `python3 tools/check_py2cpp_transpile.py` (checked=135, ok=135).
