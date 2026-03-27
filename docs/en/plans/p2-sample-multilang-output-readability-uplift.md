<a href="../../ja/plans/p2-sample-multilang-output-readability-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Multi-language sample Output Readability Degradation (Redundant Syntax Cleanup)

Last updated: 2026-03-02

Related TODO:
- `ID: P2-SAMPLE-OUTPUT-READABILITY-01` in `docs/ja/todo/index.md`

Background:
- Conservative output retained for semantic preservation still leaves many readability-harming redundant patterns across multi-language backends (unnecessary parentheses, redundant temporaries, append chains).
- This does not directly affect correctness, but it reduces visual reviewability and maintainability of generated artifacts.

Goal:
- Simplify output without changing semantics and raise baseline readability of generated artifacts in `sample/`.

Scope:
- `src/hooks/{js,ts,ruby,lua,java}/emitter/*.py`
- `sample/{js,ts,ruby,lua,java}/*.*`
- Related unit/golden tests

Out of scope:
- Correctness fixes (P0)
- Type-model redesign or runtime spec changes (beyond P1 scope)

Acceptance criteria:
- In `sample/01` and `sample/18`, redundant parentheses, redundant temporaries, and append chains are visibly reduced.
- Hard-to-read helper variables such as `const __start_N = 0` in `js/ts` are reduced.
- Append chains in `ruby/lua` are simplified (batched where possible).
- Regression tests and transpile/parity pass.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java*' -v`
- `python3 tools/regenerate_samples.py --langs js,ts,ruby,lua,java --stems 01_mandelbrot,18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets js,ts,ruby,lua,java --ignore-unstable-stdout 01_mandelbrot 18_mini_language_interpreter`

Breakdown:
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] Inventory redundant syntax patterns per language (unnecessary parentheses/helper vars/append chains) and define applicability boundaries.
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] Implement output rules simplifying loop helper vars (`__start_N`) in `js/ts`.
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] Implement output rules simplifying append chains in `ruby/lua`.
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] Implement simplification rules for redundant parentheses/step vars in `java`.
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] Add regression tests to detect readability regressions.
- [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] Regenerate target samples and verify non-regression by transpile/parity.

Decision log:
- 2026-03-02: Separated "readability-only improvements" from sample multi-language quality review as P2, and fixed an execution order that does not get mixed with correctness fixes (P0).
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] Inventory results (`sample/01,18`): major noise is `__start_N` in `js/ts` (partially required for TDZ avoidance) and `Number(...)`/cast surroundings; append chains and tuple/unpack temporaries during enumerate expansion in `ruby/lua`; and conditional `for` with `__step_N` plus excessive parentheses in `java`.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] Fixed applicability boundaries: in `js/ts`, reduce `__start_N` only when start expression does not reference loop target; in `ruby/lua`, simplify chains only for single-element push chains with side-effect-free RHS; in `java`, directize `__step_N` only for `step=1` constants and simple range comparisons, while keeping dynamic/descending conditions (fail-closed).
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] Applied direct-start fastpath in JS emitter `ForRange` (when `start` does not reference target). Because TS shares JS path, it was reflected simultaneously; confirmed no generation of `const __start_N` in `sample/{js,ts}/01,18`.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] Confirmed Ruby already degrades append chains to `owner.concat([..])` in existing implementation. Added equivalent rule to Lua, degrading chained `owner.append(x)` (owner=Name, arg=side-effect-free expression) into a single line `table.move({..}, 1, n, #(owner)+1, owner)`.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] Verification: added `test_append_chain_is_compacted_with_table_move` and it passed. Full `test_py2lua*` still fails due to known baseline failures (legacy assumptions in runtime-separation expected values), independent of this task. `test_py2rb*` passed.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] Added "constant step fastpath" in Java emitter `ForCore` / listcomp range output, changing output to omit `__step_N` for constant steps including `step=±1`. For non-constant or zero steps, kept existing dynamic ternary path (fail-closed).
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] Verification: added regressions for `for_range` and `range_downcount_len_minus1` to `test_py2java_smoke.py`, passed. Reflected in `sample/java` with `tools/regenerate_samples.py --langs java --stems 01_mandelbrot,18_mini_language_interpreter --force`.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] Regression checks: `test_py2{js,ts,rb,java}_smoke.py` passed. `test_py2lua_smoke.py` still has 7 known failures from expectations not yet updated for runtime-separation contract migration (helper-inline assumptions), independent of this task.
- 2026-03-02: [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] Ran `tools/regenerate_samples.py --langs js,ts,ruby,lua,java --stems 01_mandelbrot,18_mini_language_interpreter --force`. Ran `runtime_parity_check --targets js,ts,ruby,lua,java --ignore-unstable-stdout 01,18`; confirmed `lua` OK on both cases, and known continuing issues: `js/ts` `01` artifact size mismatch, `java` `01` artifact missing and `18` compile/run fail, `ruby` `18` tokenize run fail (tracked as separate issue streams).
