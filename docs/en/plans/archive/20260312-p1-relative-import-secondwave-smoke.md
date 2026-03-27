<a href="../../../ja/plans/archive/20260312-p1-relative-import-secondwave-smoke.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Relative-Import Second-Wave Transpile Smoke

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01` in `docs/ja/todo/index.md`

Background:
- The current relative-import coverage baseline is already locked through `cpp=build_run_locked` and `rs/cs=transpile_smoke_locked`.
- The second-wave backends (`go/java/js/kotlin/nim/scala/swift/ts`) only have rollout ordering fixed so far; their representative transpile smoke is not locked yet.
- To keep pushing a Pytra-NES-style package layout into non-C++ targets, the next step is to lock smoke on backends that already succeed through single-output transpilation.

Goal:
- Fix `js/ts` as the representative second-wave backends.
- Add representative relative-import transpile smoke and update the coverage inventory plus backend-parity handoff around that new baseline.

Scope:
- Add the second-wave representative smoke contract for `js/ts`
- Add representative relative-import backend smoke for JavaScript / TypeScript
- Update the coverage inventory / checker / backend-parity docs / handoff metadata

Out of scope:
- Adding smoke for `go/java/kotlin/nim/scala/swift`
- Expanding into build/run support claims
- Changing relative-import semantics

Acceptance criteria:
- `js` and `ts` have representative relative-import transpile smoke tests.
- The coverage inventory is locked as `js/ts=transpile_smoke_locked`, while the remaining second-wave and long-tail backends stay `not_locked` under the current handoff lanes.
- The backend-parity docs and handoff metadata match the new `js/ts` baseline plus the remaining second-wave planning handoff.

Verification commands:
- `python3 tools/check_relative_import_secondwave_smoke_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_smoke_contract.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/js -p 'test_py2js_smoke.py' -k relative_import`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/ts -p 'test_py2ts_smoke.py' -k relative_import`
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/build_selfhost.py`

Decision log:
- 2026-03-12: After TODO became empty again, the next live task was opened as second-wave representative smoke for relative imports.
- 2026-03-12: `js/ts` were fixed as the first representative second-wave backends because both canonical scenarios already transpile successfully and can be locked with single-output smoke.
- 2026-03-12: The second-wave smoke contract now lives in `relative_import_secondwave_smoke_contract.py` plus its checker and tooling test; `S1-01` is the formal close of that live contract.
- 2026-03-12: The `py2js` smoke lane now follows the second-wave contract through a shared helper so both representative scenarios stay aligned with the same expected needles.
- 2026-03-12: The `py2ts` smoke lane now uses the same shared helper as `py2js`, so both second-wave backends lock the same representative scenarios with the same expected needles.
- 2026-03-12: The coverage inventory keeps its next handoff on `P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01`, while promoting `js/ts` into the locked `transpile_smoke` baseline.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01] Lock representative relative-import transpile smoke for `js/ts` and update the coverage inventory / docs handoff to the next baseline.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S1-01] Create the live plan / TODO and lock the `js/ts` second-wave smoke contract.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-01] Add representative relative-import transpile cases to the `py2js` smoke suite.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-02] Add representative relative-import transpile cases to the `py2ts` smoke suite.
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S3-01] Sync the coverage inventory / backend-parity docs / handoff metadata to the `js/ts` baseline and leave the task close-ready.
