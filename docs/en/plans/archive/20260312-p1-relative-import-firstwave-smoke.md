<a href="../../../ja/plans/archive/20260312-p1-relative-import-firstwave-smoke.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Relative-Import First-Wave Transpile Smoke

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01` in `docs/ja/todo/index.md`

Background:
- The current relative-import coverage baseline is already locked through `cpp=build_run_locked`, and the non-C++ rollout order is already staged with `rs/cs` as the first wave.
- The implementation already works for `rs/cs`, but the project still lacks canonical backend smoke and inventory/docs handoff that would let those lanes count as verified without widening support claims.
- Before the Pytra-NES-style project layout is widened to more targets, the first-wave backends need their representative transpile smoke locked.

Goal:
- Lock representative relative-import transpile smoke for `rs/cs`.
- Update the coverage inventory, backend-parity docs, and next-rollout handoff around an `rs/cs=transpile_smoke_locked` baseline.

Scope:
- Add representative relative-import backend smoke for Rust/C#
- Update the relative-import coverage inventory / checker / docs handoff
- Document the handoff into second-wave planning

Out of scope:
- Expanding Rust/C# into build/run support claims
- Implementing the second-wave backends
- Changing relative-import semantics

Acceptance criteria:
- `rs` and `cs` have representative relative-import transpile smoke tests.
- The coverage inventory is locked as `rs/cs=transpile_smoke_locked` while every other non-C++ lane stays `not_locked`.
- The backend-parity docs and handoff metadata match the new baseline.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k relative_import`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k relative_import`
- `python3 tools/build_selfhost.py`

Decision log:
- 2026-03-12: After the TODO became empty, the next live task was defined as locking the archived non-C++ first wave into actual backend smoke plus coverage/docs handoff.
- 2026-03-12: The `rs/cs` first-wave smoke stays on the canonical `parent_module_alias` / `parent_symbol_alias` scenarios, and the coverage inventory may move to `transpile_smoke_locked` without widening the lane into a full support claim.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01] Lock representative relative-import transpile smoke for `rs/cs` and update the coverage inventory / docs handoff to the new baseline.
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S1-01] Create the live plan / TODO and fix the `rs/cs=transpile_smoke_locked` baseline plus verification lane.
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S2-01] Add representative relative-import transpile cases to the `py2rs/py2cs` smoke suites.
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S2-02] Sync the coverage inventory / backend-parity docs / handoff metadata to `rs/cs=transpile_smoke_locked`.
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S3-01] Align docs / tests / inventory to the current baseline and leave the task close-ready.
