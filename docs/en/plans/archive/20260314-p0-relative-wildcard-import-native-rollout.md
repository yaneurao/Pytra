# P0: relative wildcard import native backend rollout

Last updated: 2026-03-14

Related TODO:
- `docs/en/todo/index.md` `ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01`

Background:
- The C++ multi-file lane already locks `from .helper import *` with a representative smoke test.
- In contrast, several non-C++ native backends still return `unsupported relative import form: wildcard import` for `from ..helper import *` or `from .helper import *`.
- Ordinary relative imports already reach transpile-smoke on many backends, so wildcard relative imports are the remaining divergent contract.
- Multi-file projects such as Pytra-NES hit these surface differences directly, so relative wildcard imports need the same representative rollout treatment.

Goal:
- Support representative `from .helper import *` / `from ..helper import *` on non-C++ native backends using the existing import-resolution contract.
- Keep unresolved and duplicate-binding cases fail-closed, matching the current absolute wildcard-import behavior.

In scope:
- the relative wildcard-import lane for `go/java/kotlin/lua/nim/php/ruby/scala/swift`
- backend-native emitter / package-transpile regressions for relative wildcard imports
- syncing rollout contracts / checkers / docs / TODO

Out of scope:
- redesigning the C++ lane
- changing the semantics of absolute `from helper import *`
- rollout to `rs/cs/js/ts`
- dynamic import or runtime import hooks

Acceptance criteria:
- Representative smoke tests for the target backends must transpile `from .helper import *` or `from ..helper import *`.
- Duplicate binding, unresolved wildcard, and root-escape cases must remain fail-closed.
- Existing non-wildcard relative-import smoke tests must keep passing.
- `python3 tools/check_todo_priority.py`, focused backend smoke tests, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_relative_wildcard_import_native_rollout_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_wildcard_import_native_rollout_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-13: With TODO empty, this was opened as a `P0` follow-up close to the current Pytra-NES import blockers. The first step is to lock the exact fail-closed backend inventory, then move in backend bundles.
- 2026-03-13: `S1-01` / `S1-02` fixed the rollout bundles, evidence lanes, and current fail-closed inventory in a contract/checker/unit-test trio. The next step is to make the `go/nim/swift` native-path bundle green.
- 2026-03-13: `go/nim/swift` now rely on backend-only emitter changes: the single-file `load_east3_document(...)` lane stays fail-closed, while the module-graph `build_module_east_map(...)` lane goes green via wildcard-expanded `meta.import_symbols`. Next is the `java/kotlin/scala` package-project bundle.
- 2026-03-13: `java/kotlin/scala` now also keep the single-file `load_east3_document(...)` lane fail-closed, while the module-graph `build_module_east_map(...)` lane goes green for the representative package bundle through wildcard-expanded `meta.import_symbols`. Next is the `lua/php/ruby` long-tail bundle.
- 2026-03-14: `lua/php/ruby` also keep the single-file `load_east3_document(...)` lane fail-closed, while the module-graph `build_module_east_map(...)` lane now goes green for the representative long-tail bundle through wildcard-expanded `meta.import_symbols`. Only docs / parity sync remain.
- 2026-03-14: Synchronized the coverage / parity docs / contract handoff to the final state and closed the rollout with the representative module-graph bundle at `transpile_smoke_locked` while the single-file direct lane remains `backend_specific_fail_closed`.

## Breakdown

- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S1-01] Lock the rollout order and representative backend bundles in the plan / TODO.
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S1-02] Lock the current fail-closed backend inventory and evidence lanes with a contract / checker / unit test.
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-01] Make the `go/nim/swift` native-path bundle green for representative relative wildcard imports.
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-02] Make the `java/kotlin/scala` package-project bundle green for representative relative wildcard imports.
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S2-03] Make the `lua/php/ruby` long-tail native-emitter bundle green for representative relative wildcard imports.
- [x] [ID: P0-RELATIVE-WILDCARD-IMPORT-NATIVE-01-S3-01] Sync backend coverage / parity docs / TODO to the final state and close the task.
