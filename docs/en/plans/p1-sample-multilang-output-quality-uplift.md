<a href="../../ja/plans/p1-sample-multilang-output-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Strengthen Known-Type Fastpaths for sample Multi-language Output (Quality Uplift)

Last updated: 2026-03-02

Related TODO:
- `ID: P1-SAMPLE-OUTPUT-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- Generated code in `sample/` still has many points where known-type paths degrade to `Any/Object`, or where helper/cast calls are excessive even when semantics match.
- This is especially visible in `go/java/kotlin/swift/scala` with heavy `Any/Object` dependency, and in `rs/js/ts` with redundant loops/temporaries.

Goal:
- Prioritize native representations for known-type expressions/containers/loops to improve both readability and runtime efficiency of generated code.

Scope:
- `src/hooks/{go,java,kotlin,swift,scala,rs,js,ts}/emitter/*.py`
- `src/py2{go,java,kotlin,swift,scala,rs,js,ts}.py`
- `sample/{go,java,kotlin,swift,scala,rs,js,ts}/*.*`
- Related unit/golden tests

Out of scope:
- Spec additions (new syntax support, new built-in support)
- Large runtime API overhauls

Acceptance criteria:
- In `sample/01` and `sample/18`, known-type-path degradation to `Any/Object` and unnecessary helper calls are reduced.
- Redundant loop forms such as `for __for_i ...; i = __for_i;` and `const __start_N = 0` are degraded.
- Language-specific smoke/transpile checks and parity (at least `01/18`) pass.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts*' -v`
- `python3 tools/gen/regenerate_samples.py --langs go,java,kotlin,swift,scala,rs,js,ts --stems 01_mandelbrot,18_mini_language_interpreter --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets go,java,kotlin,swift,scala,rs,js,ts --ignore-unstable-stdout 01_mandelbrot 18_mini_language_interpreter`

Breakdown:
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-01] Inventory `Any/Object` degradation hotspots in `go/java` (`sample/18`) and fix applicability boundaries for typed fastpaths.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-02] Inventory helper/cast chains in `kotlin/swift/scala` (`__pytra_int/float`, `asInstanceOf`) and fix reduction priority order.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-03] Specify degradation rules for loop redundancy patterns in `rs/js/ts` (`__for_i` rebind, `__start_N`).
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] Implement typed container/typed access fastpaths in `go/java` emitters.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] Implement cast/helper suppression fastpaths in `kotlin/swift/scala` emitters.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] Implement canonical loop output in `rs/js/ts` emitters to remove redundant temporaries.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] Add language-specific regression tests to detect recurring degradation.
- [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-02] Regenerate target samples and verify non-regression with smoke/transpile/parity.

Decision log:
- 2026-03-02: Filed cross-language improvements centered on known-type fastpaths as P1 after sample multi-language quality review.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-01] Inventoried `sample/go/18` and `sample/java/18`. Confirmed untyped degradation for `line_index/source` in `[]any` / `ArrayList<Object>`, `map[any]any` / `HashMap<Object,Object>`, and enumerate expansion. Fixed `S2-01` applicability boundaries to: (a) resolved types of list/tuple/dict are closed, (b) loop target plan is Name/Tuple with type annotations, (c) `py_*` helper does not require object boundaries.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-02] Inventoried `sample/{kotlin,swift,scala}/18`. Identified major noise as same-type recast chains in `__pytra_int(...)`, defensive casts with `asInstanceOf` / `as? ... ??`, and `__pytra_as_list(...typed literal...)`. Fixed reduction priority as 1) remove same-type cast/helper, 2) direct typed literal output, 3) typed fastpath for container access.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-03] Inventoried `sample/{rs,js,ts}/18`. Redundant patterns are `for __for_i_N ...; i = __for_i_N` in `rs`, and `const __start_N = 0; for (let i = __start_N; ...)` in `js/ts`. Fixed `S2-03` rule as "embed constant start values directly," "bind direct range series directly to target," and "do not emit bridge vars used only for reassignment."
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] Added enumerate fastpath for `RuntimeIterForPlan + TupleTarget` in Go emitter, degrading `__pytra_enumerate` + tuple expansion (`__pytra_as_list(__it)`) to direct index/value binding (`sample/go/18`).
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] Added container type inference in Java emitter (`list[T] -> ArrayList<T>`, `dict[K,V] -> HashMap<K,V>`) and expected-type constructor correction for empty literals. Replaced `ArrayList<Object>/HashMap<Object,Object>` in `sample/java/18` with typed containers.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] Added fastpath for Java enumerate loops using typed iterator casts when list element types are known, reducing `String.valueOf(__iter.get(...))` dependency.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] Verification: `test_py2go*`/`test_py2java*` smoke passed; ran `regenerate_samples --langs go,java --stems 18_mini_language_interpreter --force`. `runtime_parity_check --targets go,java 18_mini_language_interpreter` failed on known compile blockers (go: interface field access, java: `HashMap.get(key,default)` etc.), confirmed as not regressions from this change.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] Adjusted `_expr_emits_target_type` and `int/float` call output for `kotlin/swift/scala`; after excluding helper (`__pytra_*`) and Any-return paths such as `dict.get`, allowed cast omission only for non-helper calls with known resolved types.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] Regenerated `sample/{kotlin,swift,scala}/18`. Confirmed `__pytra_int(...)` chains were removed in `let_expr_index/print_expr_index/assign_expr_index` and degraded to direct assignment.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] Verification: `test_py2kotlin*`/`test_py2swift*`/`test_py2scala*` smoke passed. Parity passed for `kotlin,scala` (`18_mini_language_interpreter`). For `swift`, parity was not run because toolchain is not installed (known constraint).
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] Added fastpath in JS emitter `ForRange` to omit `const __start_N` when `start` does not reference target name, directly emitting `for (let i = <start>; ...)`. TS improved simultaneously because it shares JS path.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] Added post-loop-target reference annotation (`rust_loop_target_used_after_stmt`) in Rust emitter. For `ForRange` with no post-use, bind directly as `for i in (start)..(stop)` (remove `__for_i`/reassign). Preserve existing path when post-use exists for fail-closed behavior.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] Verification: `test_py2rs*`/`test_py2js*`/`test_py2ts*` smoke passed. Regenerated `01/18` for `sample/{rs,js,ts}` and confirmed `__for_i` and `const __start_N` were degraded in target cases. `runtime_parity_check --targets rs,js,ts 01/18` failed on known `artifact_size_mismatch` in `js/ts` (`01`), confirmed not a new compile/runtime failure from this change.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] Added regression tests: `js/ts` fix direct start embedding fastpath and TDZ-avoidance condition for keeping `__start_N`; `rs` fixes "direct bind when post-use absent" and "keep bridge (`__for_i`) when post-use exists."
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] Node `meta` augmentation cannot persist Rust post-use detection (`any_to_dict_or_empty` returns a copy), so implemented "search subsequent statements of current statement" via block-context stack in `emit_stmt_list` to guarantee fail-closed behavior.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] Verification: ran `test_py2rs_smoke.py` (34), `test_py2js_smoke.py` (26), `test_py2ts_smoke.py` (18), all passed.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-02] Ran `regenerate_samples --langs go,java,kotlin,swift,scala,rs,js,ts --stems 01_mandelbrot,18_mini_language_interpreter --force`. Reflected regenerated diffs and synced `sample` outputs with current emitter state.
- 2026-03-02: [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-02] Verification: all `test_py2{go,java,kotlin,swift,scala,rs,js,ts}*` smoke passed (165 total). `runtime_parity_check` failed on known constraints (go/java: compile/run blockers, js/ts: 01 artifact_size_mismatch, swift: toolchain_missing), confirming no new smoke regression from this change.

Implementation boundary notes (S1 aggregate):
- `go/java` typed fastpaths prioritize containers and loop targets in `tokenize/parse_program/execute/build_benchmark_source`.
- `kotlin/swift/scala` cast/helper reduction prioritizes `int64`-known paths in `parse_*` / `eval_expr`, and keeps fail-closed behavior at object boundaries (dict/dynamic index).
- `rs/js/ts` loop degradation is limited to simple ranges derived from `StaticRangeForPlan`; paths with non-constant `step` or swapped comparison expressions are excluded.
