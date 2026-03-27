<a href="../../ja/plans/p0-regenerate-samples-scala-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Add Scala Support to `regenerate_samples.py`

Last updated: 2026-03-02

Related TODO:
- `ID: P0-REGEN-SCALA-SUPPORT-01` in `docs/ja/todo/index.md`

Background:
- When updating `sample/scala` from `sample/py`, currently `tools/regenerate_samples.py` does not include `scala` in its language list.
- As a result, only Scala has a split regeneration path, and sample-update operations and regression procedures are inconsistent with other languages.

Goal:
- Officially support `--langs scala` in `tools/regenerate_samples.py` and integrate `sample/scala` regeneration into the existing path.

In scope:
- `tools/regenerate_samples.py`
- `src/pytra/compiler/transpiler_versions.json` as needed (version token dependency definition)
- Regeneration check for `sample/scala`
- Related unit/smoke checks (minimum needed)

Out of scope:
- Scala emitter feature expansion
- Scala parity spec changes
- Redesign of non-Scala backends

Acceptance criteria:
- `python3 tools/regenerate_samples.py --langs scala --force` succeeds and can batch-regenerate `sample/scala/*.scala`.
- `scala` is no longer treated as invalid in `--langs` validation.
- `scala` is wired into version-token checks so skip/regen decisions work in non-force runs.
- No regression on existing language paths (at least `cpp` and `go`).

Verification commands (planned):
- `python3 tools/regenerate_samples.py --langs scala --force`
- `python3 tools/regenerate_samples.py --langs scala --dry-run --verbose`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`

Breakdown:
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S1-01] Audit `LANG_CONFIGS` / `LANG_VERSION_DEPENDENCIES` / `--langs` default, and finalize Scala-addition policy.
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S2-01] Add `scala` config to `tools/regenerate_samples.py` so CLI accepts `--langs scala`.
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S2-02] Wire `scala` into version-token checks and enable cache-based skip/regen judgment.
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S3-01] Regenerate `sample/scala` and confirm generated diffs update as expected.
- [x] [ID: P0-REGEN-SCALA-SUPPORT-01-S3-02] Run smoke/check and confirm no regressions.

Decision log:
- 2026-03-02: Per user instruction, fixed `regenerate_samples.py` Scala non-support as prioritized P0.
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S1-01] Confirmed `scala` was not wired in `LANG_CONFIGS` / `LANG_VERSION_DEPENDENCIES` / `--langs` defaults, and fixed policy to connect `src/py2scala.py` + `sample/scala/*.scala` + `transpiler_versions.json.languages.scala`.
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S2-01] Added Scala config in `tools/regenerate_samples.py` (`cli=src/py2scala.py`, `out_dir=sample/scala`, `ext=.scala`) and to `--langs` defaults, resolving `unknown language(s): scala`.
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S2-02] Added `scala` to `LANG_VERSION_DEPENDENCIES` and `languages.scala=0.1.0` to `src/pytra/compiler/transpiler_versions.json`, enabling version-token checks.
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S3-01] Ran `python3 tools/regenerate_samples.py --langs scala --force` and confirmed `summary: total=18 skip=0 regen=18 fail=0`.
- 2026-03-02: [ID: P0-REGEN-SCALA-SUPPORT-01-S3-02] Confirmed `--langs scala --dry-run --verbose` (18 skips), `--langs cpp,go --dry-run` (fail=0), and `test_py2scala_smoke` pass (17 cases).
