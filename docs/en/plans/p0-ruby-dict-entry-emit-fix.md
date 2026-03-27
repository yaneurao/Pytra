<a href="../../ja/plans/p0-ruby-dict-entry-emit-fix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Fix Ruby Dict Literal Emit (EAST3 `entries`)

Last updated: 2026-03-04

Related TODO:
- `ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01` in `docs/ja/todo/index.md`

Background:
- In `P0-RUBY-S18-TOKENIZE-INVEST-01`, the direct cause of Ruby failure for `sample/18` was identified.
- EAST3 `Dict` nodes have an `entries` array, but `_render_dict_expr` in `src/toolchain/emit/ruby/emitter/ruby_native_emitter.py` references only the old `keys/values` format.
- As a result, `single_char_token_tags: dict[str, int] = {...}` becomes `{}` in generated Ruby code, `=` token recognition breaks, and execution stops at `tokenize error at line=0 pos=6 ch==`.

Goal:
- Make Ruby emitter dict-literal generation correctly follow EAST3 `entries`.
- Resolve Ruby parity failure on `sample/18`.

In scope:
- `src/toolchain/emit/ruby/emitter/ruby_native_emitter.py`
- Ruby regression cases for dict literal in `test/fixtures` or `test/unit`
- Ruby revalidation for `sample/18` using `tools/runtime_parity_check.py`

Out of scope:
- Overall Ruby backend optimization
- Performance improvements outside `sample/18`
- Simultaneous emitter changes for other languages

Acceptance criteria:
- Ruby emitter correctly outputs EAST3 `Dict(entries=...)` as `{ k => v, ... }`.
- A minimal dict-literal repro test can detect if Ruby output collapses to `{}`.
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter` passes.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_smoke.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter`

Decision log:
- 2026-03-04: Opened as follow-up implementation for `P0-RUBY-S18-TOKENIZE-INVEST-01`. Fix scope is limited to `entries` support in `_render_dict_expr`.
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-01] Refactored `_render_dict_expr` to prioritize `entries` with fallback support for old `keys/values`. Confirmed restored generation in `sample/18`: `single_char_token_tags = { "+" => 1, ... "=" => 7 }`.
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-02] Added regression tests `test/fixtures/core/dict_literal_entries.py` and `test_py2rb_smoke.py`, making it possible to verify dict literals do not collapse to `{}`.
- 2026-03-04: [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S2-01] Re-ran `runtime_parity_check --case-root sample --targets ruby 18_mini_language_interpreter` and confirmed pass (1/1). Also confirmed no regression on `check_py2rb_transpile` (133/133) and `test_py2rb_smoke` (25 tests).

## Breakdown

- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-01] Render `_render_dict_expr` with `entries` priority and keep old `keys/values` as backward-compatible path.
- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-02] Add minimal dict-literal repro fixture and Ruby conversion regression tests.
- [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S2-01] Re-run Ruby parity on `sample/18` and confirm failure resolution.
