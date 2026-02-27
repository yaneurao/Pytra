# TASK GROUP: TG-P3-MISC-EXT

Last updated: 2026-02-25

Related TODO:
- `ID: P3-MISC-02` in `docs/ja/todo/index.md`

Background:
- Existing 100 files under `test/misc/*.py` were already processed, but another 400 files were added, so we need to re-establish `py2cpp.py` transpile feasibility under the same criteria.
- `test/misc` is also source-diff regression material, so `test/misc/*.py` itself must not be modified while running this task.

In scope:
- Added 400 files corresponding to `test/misc/101_*.py` through `test/misc/500_*.py`

Out of scope:
- Quality optimization of generated `test/misc` artifacts (`.cpp`).
- Multi-language transpilation.

Acceptance criteria:
- For each of the 400 files, `python3 src/py2cpp.py test/misc/<file>.py /tmp/<base>.cpp` succeeds.
- Failure cases are recorded incrementally in the decision log of `docs/ja/plans/p3-misc-extended-transpile.md`; same root causes should be fixed in grouped form.

Constraints:
- Do not edit `test/misc/*.py` for this task.
- Fixes for transpile failures should be done in `py2cpp.py` / parser / `CodeEmitter` / shared foundation.
- At each `S*` task completion, append the successful conversion logs and commands for target files.

Decision log:
- (Unstarted at the time this task group was added. Append progressively after completion.)
