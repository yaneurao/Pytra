<a href="../../ja/plans/p0-ruby-s18-tokenize-parity-investigation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Investigate Ruby `sample/18` Parity Failure (`tokenize error`)

Last updated: 2026-03-04

Related TODO:
- `ID: P0-RUBY-S18-TOKENIZE-INVEST-01` in `docs/ja/todo/index.md`

Background:
- In `tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples`, only `18_mini_language_interpreter` fails.
- The failure is `tokenize error at line=0 pos=6 ch==` at Ruby runtime, categorized as `run_failed`.
- The parity validation script already purges artifacts beforehand, so this failure is not caused by stale artifacts.

Goal:
- Identify the root cause of Ruby backend failure on `sample/18` (lower / emitter / runtime / generated code).
- Extract a reproducible minimal case and finalize the remediation policy.

In scope:
- `sample/py/18_mini_language_interpreter.py`
- `sample/ruby/18_mini_language_interpreter.rb` (regenerate as needed)
- Ruby backend (lower / emitter) and related runtime helpers
- Parity failure log (`work/logs/runtime_parity_ruby_sample_after_artifact_purge_20260303.json`)

Out of scope:
- Overall Ruby backend optimization
- Speed improvements for other cases (`01` to `17`)
- Updating README runtime table

Acceptance criteria:
- The direct failure cause can be explained with code locations (identify which conversion rule breaks it).
- A minimal repro case can be defined (fixture or sample fragment).
- Fix policy (implementation layer, impact scope, regression-test addition points) can be recorded in decision log.
- If needed, follow-up fix tasks can be split and opened as P0/P1.

Verification commands (planned):
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 18_mini_language_interpreter`
- `python3 tools/regenerate_samples.py --langs ruby --stems 18_mini_language_interpreter --force`
- `ruby sample/ruby/18_mini_language_interpreter.rb`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`

Decision log:
- 2026-03-03: Per user instruction, opened this as P0 root-cause investigation for Ruby parity failure (`tokenize error`) in `sample/18`.
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] Reproduced `tokenize error at line=0 pos=6 ch==` with both `runtime_parity_check --case-root sample --targets ruby 18_mini_language_interpreter` and `ruby out/ruby_validate/18_mini_language_interpreter.rb`. Input head line is `let a = 10`; in generated Ruby, `single_char_token_tags = {}` (missing `=` dict registration).
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] With same input `let a = 10`, Python tokenize returns `LET, IDENT, EQUAL, NUMBER...`, while Ruby version stops at `pos=6 ('=')`. First divergence point is fixed as initialization of `single_char_token_tags` (Python: `{'=':7,...}` / generated Ruby: `{}`).
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] Identified responsible rule as Ruby emitter `Dict` rendering. EAST3 `Dict` uses `entries`, but `ruby_native_emitter._render_dict_expr` referenced only old `keys/values`, returning `{}`.
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] Judged minimal repro as sufficient with policy "initialize typed dict literal and read with `.get()`" (`d: dict[str, int] = {"=": 7}; print(d.get("=", 0))`). Chose fixture focused on dict-literal path only, not full `tokenize`.
- 2026-03-04: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] Finalized fix policy as `Ruby emitter Dict(entries) support + fixture regression + sample/18 parity revalidation`, and opened implementation task `P0-RUBY-DICT-ENTRY-EMIT-FIX-01` in TODO.

## Breakdown

- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] Reproduce parity failure, collect exception location and input token sequence.
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] Compare Python and Ruby tokenize results and identify the first divergence point.
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] Identify the conversion rule causing divergence (lower/emitter/runtime) and clarify ownership boundary.
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] Draft plan to add minimal repro case to `test/fixtures` and decide required verification granularity.
- [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] Finalize fix policy (implementation points/out-of-scope/regression tests) and open follow-up fix task.
