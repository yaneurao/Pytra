<a href="../../docs-ja/plans/archive/p1-multilang-output-quality.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-MULTILANG-QUALITY

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo/index.md` `ID: P1-MQ-01` to `P1-MQ-08`

Background:
- Compared with `sample/cpp/`, generated code in `sample/rs` and other languages (`cs/js/ts/go/java/swift/kotlin`) shows notable readability regressions.
- Unnecessary `mut`, excessive parentheses/casts/clones, and unused imports increase review and maintenance costs.
- Outside C++, selfhost and multi-stage selfhost feasibility is not yet systematically tracked.
- Running Python every time for `sample/py` comparisons increases verification time; a golden-output reuse path is needed.

Objective:
- Incrementally raise non-C++ generated code quality to the same readability level as `sample/cpp/`.

In scope:
- Output-quality improvement for `sample/{rs,cs,js,ts,go,java,swift,kotlin}`
- Reducing redundant output patterns in each language's emitter/hooks/profile
- Adding checks to prevent quality regressions
- Verifying selfhost feasibility for non-C++ languages (re-transpile via self-generated artifacts)
- Verifying multi-stage selfhost for non-C++ languages

Out of scope:
- Semantic changes in generated code
- Adding runtime features themselves
- Additional optimization for C++ output

Acceptance criteria:
- Major redundancy patterns in non-C++ `sample/` outputs (excess `mut` / parentheses / cast / clone / unused imports) are reduced incrementally.
- Existing transpile/smoke checks continue to pass after readability improvements.
- Quality metrics and measurement procedures are documented and reproducible for regressions.
- For each non-C++ language, selfhost and multi-stage selfhost status (stage-1/stage-2) are logged in a unified format.
- For failed languages, reproduction steps and failure category (transpile failure / runtime failure / compile failure / output mismatch) are recorded.
- No nondeterministic info (timestamps, etc.) is embedded in `sample/` artifacts; CI regeneration remains diff-free.
- Golden-output storage/update procedure for `sample/py` is documented so routine verification does not require running Python every time.

Validation commands:
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`

Decision log:
- 2026-02-22: Initial draft (set `sample/cpp` quality as target for non-C++ outputs).
- 2026-02-22: For `P1-MQ-08`, switched `tools/verify_sample_outputs.py` to golden-based operation. Default now compares against `sample/golden/manifest.json` + C++ execution results, and Python execution runs only with `--refresh-golden` (or `--refresh-golden-only` for update-only mode).
