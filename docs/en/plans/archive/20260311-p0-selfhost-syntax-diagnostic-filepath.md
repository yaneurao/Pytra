<a href="../../../ja/plans/archive/20260311-p0-selfhost-syntax-diagnostic-filepath.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Always attach file:line:col to self-hosted parser syntax errors

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` `ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01`

Background:
- The CLI already wraps self-hosted parser syntax failures as `user_syntax_error`, but some detail lines still lose the input filename.
- A representative case is `unsupported_syntax: self_hosted parser cannot parse expression token: * at 749:18`, which only shows line/column and not the failing file.
- Import diagnostics are already more structured with `file=...`, so syntax-only path loss is an unnecessary UX regression that slows debugging of real experiments.

Goal:
- Make self-hosted parser syntax errors always report a detail line with `file:line:col`.
- Improve only the syntax lane without breaking the current import-diagnostics and structured user-error contracts.

In scope:
- Self-hosted syntax-error classification inside `transpile_cli.load_east_document()`
- A helper that preserves file path, line, and column in the detail line
- Representative CLI / unit regressions
- Keeping ja/en TODO / plan / docs synchronized

Out of scope:
- Redesigning import diagnostics
- Changing host-Python `SyntaxError` formatting
- Editor integration or a JSON diagnostics protocol

Acceptance criteria:
- `unsupported_syntax: ... at line:col` errors from the self-hosted parser always include the input path in the CLI detail line.
- Existing import-related `input_invalid` / `unsupported_import_form` contracts remain unchanged.
- Representative unit tests and selfhost build pass.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `git diff --check`

Decision log:
- 2026-03-11: v1 is limited to the self-hosted syntax lane and guarantees `file=... at line:col` in the detail line. Import-diagnostics redesign stays out of scope.
- 2026-03-11: `load_east_document()` now keeps import diagnostics ahead of syntax wrapping, then normalizes only token-mismatch errors (`expected token ...` / `cannot parse expression token: ...`) through a `path:line:col: message` helper. It does not reclassify every `unsupported_syntax` case.

## Breakdown

- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S1-01] Lock the current syntax-error gap and representative message contract in the plan/TODO.
- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S2-01] Add a self-hosted syntax-error helper and make `load_east_document()` file-aware for that lane.
- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S3-01] Refresh representative unit/CLI regressions and docs, then close the task.
