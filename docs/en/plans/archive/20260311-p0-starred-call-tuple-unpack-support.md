# P0: Support fixed-tuple starred call unpack across targets

Last updated: 2026-03-11

Related TODO:
- `docs/en/todo/index.md` `ID: P0-STARRED-CALL-TUPLE-UNPACK-01`

Background:
- The current self-hosted parser cannot parse `*expr` in call-argument position, so code such as `f(*t)` fails with `unsupported_syntax: self_hosted parser cannot parse expression token: *`.
- Experiments such as Pytra-NES need the representative case `t: tuple[int, int, int]` passed as `f(*t)`, and that gap currently blocks all-target smoke.
- The repo already has partial analysis-side handling for `Starred`, but parser, lowering, and backend-smoke contracts are not closed yet.

Goal:
- Support representative v1 call unpack for typed fixed tuples from the self-hosted parser through all backend lanes.
- Avoid per-backend special cases by normalizing starred tuple args into positional args during EAST2->EAST3 lowering.

In scope:
- Parser / AST-builder support for `*expr` in call-argument position
- EAST2->EAST3 lowering for `Starred(value=t)` where `t: tuple[...]`
- Representative fixture / parser regression / lowering regression for `t: tuple[int, int, int]; f(*t)`
- All-target smoke plus C++ runtime regression
- Keeping ja/en TODO / plan / docs synchronized

Out of scope:
- Starred unpack inside list / dict / set literals
- Assignment-target forms such as `a, *rest = xs`
- `**kwargs` unpack
- Dynamic-length tuples or `Any/object` receivers

Acceptance criteria:
- The self-hosted parser accepts `f(*t)` and preserves a `Starred` node in the call-argument lane.
- For the representative `t: tuple[int, int, int]` case, EAST2->EAST3 lowering normalizes the call into three positional args.
- The representative fixture passes in the C++ runtime lane and the major backend smoke suites.
- Unsupported lanes (non-tuple, dynamic tuple, `**kwargs`) stay fail-closed instead of silently falling back.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core_parser_behavior_exprs.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends -p 'test_py2*_smoke.py' -k starred_call_tuple`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k starred_call_tuple`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Decision log:
- 2026-03-11: v1 is intentionally limited to typed fixed-tuple call unpack. The parser preserves `Starred`, and EAST2->EAST3 lowering expands it into positional args instead of relying on backend-specific lowering.
- 2026-03-11: The representative smoke contract is `transpile success + no raw "*receiver" leak`; backend lanes that intentionally emit an empty file are not required to include non-empty source text.
- 2026-03-11: A representative regression exposed a missing `_const_int_node` import; the task was archived only after parser, lowering, all-target transpile, and C++ runtime regressions all passed again.

## Breakdown

- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S1-01] Lock the parser/AST contract for `Starred`, the representative fixture, and the unsupported lanes in the plan/TODO.
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S2-01] Add self-hosted parser and AST-builder support for call-arg `Starred`, then pass parser-behavior regressions.
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S2-02] Expand fixed-tuple starred args into positional args during EAST2->EAST3 lowering and add representative lowering regressions.
- [x] [ID: P0-STARRED-CALL-TUPLE-UNPACK-01-S3-01] Refresh the representative fixture, all-target smoke, C++ runtime regression, and docs, then close the task.
