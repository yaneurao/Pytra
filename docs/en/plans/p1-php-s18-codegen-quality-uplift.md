<a href="../../ja/plans/p1-php-s18-codegen-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Improve PHP Code Generation for `sample/18` (Runnable + Higher Quality)

Last updated: 2026-03-03

Related TODO:
- `ID: P1-PHP-S18-CODEGEN-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/php/18_mini_language_interpreter.php` is currently non-runnable due to semantic breakage in generated code.
- Concrete examples: dict literals collapse into empty arrays, `x in env` collapses into array-equivalence comparison, constructor contracts for `Token/ExprNode/StmtNode` are missing, and entrypoint name collisions occur.
- In this state, continued runtime measurement, parity comparison, and quality evaluation for PHP in `sample/18` cannot proceed.

Goal:
- Make PHP generated code for `sample/18` runnable, then improve code quality (readability/maintainability) while preserving semantic compatibility.
- Limit changes to the minimum scope reproducible in `sample/18`, with staged fail-closed application.

In scope:
- `src/toolchain/emit/php/emitter/php_native_emitter.py`
- `src/runtime/php/pytra/py_runtime.php` (minimum helper additions only if needed)
- `test/unit/test_py2php_smoke.py` (add PHP codegen regressions if needed)
- `sample/php/18_mini_language_interpreter.php` (validation by regeneration)

Out of scope:
- Full optimization of the PHP backend
- Large behavioral changes outside `sample/18`
- Image runtime implementation (full PNG/GIF writer implementation)

Acceptance criteria:
- `sample/php/18_mini_language_interpreter.php` runs to completion without runtime errors and prints `elapsed_sec`.
- `runtime_parity_check --case-root sample --targets php --ignore-unstable-stdout 18_mini_language_interpreter` passes.
- The following codegen quality conditions are satisfied:
  - `single_char_token_tags` is generated as a dictionary with expected keys, not an empty array.
  - `name in env` / `name not in env` are lowered to correct PHP array-membership checks.
  - Constructor calls and class definitions for `Token/ExprNode/StmtNode` are consistent.
  - Entrypoint generation avoids collisions when `main`/`__pytra_main` names conflict.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/regenerate_samples.py --langs php --stems 18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --ignore-unstable-stdout 18_mini_language_interpreter`

Decision log:
- 2026-03-02: Per user instruction, opened a P1 plan for PHP code generation improvements on `sample/18`.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S1-01] Reproduced failure fragments from old `sample/php/18` (dict-to-empty-array collapse / membership breakage / dataclass ctor mismatch) and fixed improvement boundaries.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-01] Enabled output for `Dict` `entries` format and correctly generated associative-array literals.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-02] Fixed `Compare(In/NotIn)` to type-specific membership lowering, using `array_key_exists` for `dict`.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-03] Added field declarations + auto `__construct` generation for dataclass classes to align ctor contracts.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-04] Generalized collision avoidance in entrypoint-name resolution for function/class names.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-01] Added `sample/18` quality-fragment checks to `tools/check_py2php_transpile.py`.
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-02] Passed `runtime_parity_check` (php, case18) after regenerating `sample/php/18`.

## Breakdown

- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S1-01] Inventory failure fragments in `sample/18` (dict literal / membership / ctor / entrypoint) and fix improvement boundaries.
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-01] Fix dict-literal output in PHP emitter to correctly generate keyed associative arrays.
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-02] Fix lowering for `in` / `not in` by type, and unify dict membership with `array_key_exists` patterns.
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-03] Align field/constructor generation for dataclass-derived classes (`Token/ExprNode/StmtNode`).
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-04] Generalize entrypoint collision avoidance in `main_guard` output and guarantee no collision in `sample/18`.
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-01] Add unit/smoke regressions and lock recurrence detection for this class of breakage (dict/in/ctor/entrypoint).
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-02] Confirm no regression by regenerating `sample/php/18` and running parity.
