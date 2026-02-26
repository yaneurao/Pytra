<a href="../../docs-ja/plans/archive/p3-pythonic-restoration.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P3-PYTHONIC

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo/index.md` `ID: P3-PY-*`, `P3-CE-*`, `P3-RULE-*`

Background:
- Readability dropped because many simplified patterns were introduced to stabilize selfhost.

Objective:
- Gradually restore more Pythonic notation while preserving selfhost stability.

In scope:
- Simplifying loops/comparisons/literals/expressions in `src/py2cpp.py`
- Consolidating duplicated checks and branch logic in `code_emitter.py`
- Small-patch operation (1 to 3 functions per patch)

Out of scope:
- Large one-shot refactors

Acceptance criteria:
- Better readability without regressing selfhost stability
- Required verification commands pass for each patch

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

Decision log:
- 2026-02-22: Initial draft created.
- 2026-02-22: `P3-PY-02` small patches restored slice-based single-char checks to `startswith` / `endswith` where selfhost-safe (`_render_set_literal_repr`, `_emit_target_unpack`, and related type-name handling).
- 2026-02-22: `P3-CE-01` to `P3-CE-04` completed through incremental patches in `code_emitter.py`:
  - Converted index-based loops to `for` where safe.
  - Added `_is_empty_dynamic_text` to centralize repeated empty-value checks.
  - Split directive/blank handling out of `_emit_trivia_items`.
  - Added `_lookup_hook` and removed repeated hook lookup patterns.
- 2026-02-22: `P3-PY-01` continued in many small steps, converting selected index-based `while` loops to `for`/`range`/`enumerate` while keeping index-style where selfhost type inference is fragile.
- 2026-02-22: `P3-PY-03` continued with staged dict-literal rewrites across `py2cpp.py` (`_parse_user_error`, `_prepare_call_parts`, module index/schema/manifest paths, etc.) while preserving selfhost-safe exceptions.
- 2026-02-22: `P3-PY-05` continued to reduce temporary `obj -> isinstance -> assign` patterns by introducing helper-based extraction (`_dict_any_get_str`, `_dict_any_get_dict`) and applying it incrementally across import/deps/meta paths.
- 2026-02-22: Regression checks were executed at each patch unit, with known selfhost diff baseline kept at `mismatches=3` (allow-not-implemented mode), and transpiler version updates tracked through `tools/check_transpiler_version_gate.py`.
