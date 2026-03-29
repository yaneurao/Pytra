<a href="../../ja/plans/p2-scala-negative-fixture-fail-assertion.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Remove `skip` from Scala Negative Fixtures and Convert to Failure-Expected Assertions

Last updated: 2026-03-02

Related TODO:
- `ID: P2-SCALA-NEGATIVE-ASSERT-01` in `docs/ja/todo/index.md`

Background:
- `tools/check/check_py2scala_transpile.py` currently excludes fixtures in `DEFAULT_EXPECTED_FAILS` as `skipped`, so it does not verify that negative cases actually fail.
- As a result, changes in failure reasons and inconsistencies in negative cases (e.g., fixtures that already pass but remain listed) are hard to detect, weakening quality assurance.
- Per user requirement, adopt the policy: "negative cases must be explicitly tested as compile errors, not skipped."

Goal:
- Operate Scala negative fixtures as "failure-expected test targets" instead of "excluded".
- Fix failure classes (parser constraints/type constraints/object receiver constraints, etc.) so deviations in failure messages can be caught by regressions.

Scope:
- Rework expected-fail operations in `tools/check/check_py2scala_transpile.py`
- Scala negative-check path (failure-expected)
- Inventory negative fixtures and remove stale entries
- Update CI/local procedure (positive checks + negative checks)

Out of scope:
- Feature additions in Scala backend itself (new implementations for `*args`/`**kwargs`/positional-only)
- Unifying negative-case operations for other backends (C++/Rust, etc.)
- Mass addition of negative fixtures (keep minimal representative cases)

Acceptance criteria:
- When running `tools/check/check_py2scala_transpile.py`, known negative cases are evaluated as failure-expected, not simple `skip`.
- If a known negative case unexpectedly succeeds, it is detected as failure (`unexpected pass`).
- If a known negative case fails with mismatched expected failure class, it is detected as failure.
- Positive fixtures/samples continue to succeed as before.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_check_py2scala_transpile.py' -v`

Decision log:
- 2026-03-01: Based on user direction, filed P2 to stop excluding Scala negative fixtures with `skip` and instead verify "expected failure".
- 2026-03-02: Inventoried negative fixtures and fixed expected failure classes to `user_syntax_error` (`ng_kwargs/ng_posonly/ng_varargs`) and `unsupported_by_design` (`ng_object_receiver/any_class_alias`).
- 2026-03-02: Removed `ng_untyped_param.py` from expected failures as a stale entry because it passes in current implementation.
- 2026-03-02: Updated `tools/check/check_py2scala_transpile.py` from skip-mode to fail-closed verification. Expected failures are always evaluated, and `unexpected pass` / `unexpected error category` / `unexpected error detail` are treated as failures.
- 2026-03-02: Added `test_check_py2scala_transpile.py` and locked regressions for category extraction, expected-failure judgment, and stale-entry reintroduction prevention.
- 2026-03-02: Updated Scala procedure in `docs/ja/how-to-use.md` / `docs/en/how-to-use.md`, documenting a one-command operation in `check_py2scala_transpile.py` for "positive success + known-negative failure-category match".

## Breakdown

- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-01] Inventory current failure reasons of Scala negative fixtures and fix expected failure classes (parser/type/object constraints).
- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-02] Remove stale entries (already-passing fixtures) from `DEFAULT_EXPECTED_FAILS` and refresh negative fixture set.
- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-01] Rebuild `check_py2scala_transpile.py` into dual verification mode: positive success + negative failure-expected.
- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-02] Fail fail-closed on negative `unexpected pass` / `unexpected error category`.
- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-01] Add unit tests to ensure negative-fixture operation does not revert to `skip`.
- [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-02] Update Scala verification steps in `docs/ja/how-to-use.md` and `docs/en/how-to-use.md`, documenting execution order (positive/negative).
