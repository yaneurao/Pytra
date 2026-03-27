<a href="../../../ja/plans/archive/20260313-p0-pytra-nes2-crossbackend-repro-contract.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Promote the Pytra-NES2 repro bundle into a representative cross-backend contract

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` item `ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01`

Background:
- `materials/refs/from-Pytra-NES2/` contains minimal repro cases cut out from stops another team hit while trying `Pytra -> C++ -> g++`.
- As of 2026-03-13, local inspection shows that `bytes_truthiness.py`, `path_stringify.py`, and `field_default_factory_rc_obj.py` no longer reproduce on the current repo because they have already been absorbed into representative fixtures, smoke tests, and archived tasks.
- In contrast, `property_method_call.py` still reproduces a C++ compile error where an `@property` read is lowered like a method object, and `list_bool_index.py` still reproduces a compile error where `list[bool]` read/write collides with the `std::vector<bool>` proxy lane.
- Closing those two as C++-only bugs would miss equivalent semantic breakage on other backends. The user instruction is to add tests first and make “the same representative test is green in all languages” the close condition.
- This P0 therefore promotes the Pytra-NES2 repro bundle from `materials/refs/` into `test/fixtures/` and backend smoke so that `@property` reads and `list[bool]` index read/write become shared representative contracts.

Goal:
- Promote `property_method_call.py` and `list_bool_index.py` into shared representative fixtures.
- Lock the same semantics not only for C++, but for `cpp`, `cs`, `rs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, and `php`.
- Keep “the representative test is green in all languages” as the close condition instead of closing on a C++-only fix.

Scope:
- `materials/refs/from-Pytra-NES2/{property_method_call.py,list_bool_index.py}`
- new representative fixtures under `test/fixtures/**`
- backend smoke:
  - `test/unit/backends/cpp/test_py2cpp_features.py`
  - `test/unit/backends/cs/test_py2cs_smoke.py`
  - `test/unit/backends/rs/test_py2rs_smoke.py`
  - `test/unit/backends/go/test_py2go_smoke.py`
  - `test/unit/backends/java/test_py2java_smoke.py`
  - `test/unit/backends/kotlin/test_py2kotlin_smoke.py`
  - `test/unit/backends/scala/test_py2scala_smoke.py`
  - `test/unit/backends/swift/test_py2swift_smoke.py`
  - `test/unit/backends/nim/test_py2nim_smoke.py`
  - `test/unit/backends/js/test_py2js_smoke.py`
  - `test/unit/backends/ts/test_py2ts_smoke.py`
  - `test/unit/backends/lua/test_py2lua_smoke.py`
  - `test/unit/backends/rb/test_py2rb_smoke.py`
  - `test/unit/backends/php/test_py2php_smoke.py`
- common smoke helpers / fixture lookup / backend contract checkers where needed
- docs / support wording / TODO

Out of scope:
- Re-fixing `bytes_truthiness.py`, `path_stringify.py`, or `field_default_factory_rc_obj.py`
- `materials/refs/from-Pytra-NES2/path_alias_pkg/entry.py`
- Implementing the backend fixes in this slice
- Archiving the whole repro bundle at once

Acceptance criteria:
- `property_method_call.py` and `list_bool_index.py` are added as representative fixtures under `test/fixtures/`.
- The expected semantics are written down in docs, test names, and assertions.
  - `property_method_call`: an `@property` read is evaluated as a value; comparisons and `str(...)` must not treat it as a method object.
  - `list_bool_index`: `list[bool]` index read and write both work, and re-reading after `not` assignment returns the updated value.
- Every target backend gets at least one representative smoke or contract test that touches those fixtures.
- The close condition is “the representative tests are green on every target backend”, not “C++ is green”.
- Falling back to `unsupported`, `preview_only`, or `not_implemented` is not an acceptable close state.
- The relation between the original repro bundle and the promoted fixtures/tests can be traced in docs or the decision log.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/go -p 'test_py2go_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/java -p 'test_py2java_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/kotlin -p 'test_py2kotlin_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/scala -p 'test_py2scala_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/swift -p 'test_py2swift_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/nim -p 'test_py2nim_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/js -p 'test_py2js_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/ts -p 'test_py2ts_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/lua -p 'test_py2lua_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/rb -p 'test_py2rb_smoke.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/php -p 'test_py2php_smoke.py'`
- `git diff --check`

Implementation policy:
1. Keep `materials/refs/` as the original external report, but treat the promoted representative fixtures/tests as the canonical lane inside the repo.
2. Add fixtures and cross-backend smoke first, then fix the implementations.
3. Even when a case reproduces today as a C++ compile error, the task still means “all backends satisfy the same semantics”, not “fix C++ only”.
4. Do not accept per-backend unsupported escape hatches; keep “all representative tests green” as the parent close condition.
5. This task is a parent integration task. Child backend slices may be split out, but the parent close condition stays unchanged.

## Current repro inventory

| README entry | current bundle | current repo status | representative lane |
| --- | --- | --- | --- |
| `bytes_truthiness.py` | present | covered elsewhere | `test/fixtures/typing/bytes_truthiness.py` + C++ representative smoke |
| `path_stringify.py` | present | covered elsewhere | `test/fixtures/stdlib/path_stringify.py` + C++ representative smoke |
| `field_default_factory_rc_obj.py` | present | covered elsewhere | archived C++ representative lane (`field(default_factory=...)` on `rc<T>`) |
| `property_method_call.py` | present | promoted and green | `test/fixtures/typing/property_method_call.py` + representative smoke across all backends |
| `list_bool_index.py` | present | promoted and green | `test/fixtures/typing/list_bool_index.py` + representative smoke across all backends |
| `path_alias_pkg/entry.py` | missing | not triaged | out of scope until the bundle includes the file |

## Representative semantics

### `property_method_call`

source:
- `materials/refs/from-Pytra-NES2/property_method_call.py`

Target semantics:
- `@property` member access is treated as a value read.
- `self.mapper == 4` compares the getter result and `4`.
- `str(self.mapper)` stringifies the getter result.
- It must not be lowered as a method symbol, callable object, or bound method.

### `list_bool_index`

source:
- `materials/refs/from-Pytra-NES2/list_bool_index.py`

Target semantics:
- `current = flags[index]` works as a read.
- `flags[index] = not current` works as a write.
- Re-reading `flags[index]` after the write returns the updated value.
- `list[bool]` must not become a special broken lane just because the backend uses a proxy-based container.

## Breakdown

- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01] Promote the Pytra-NES2 repros into a representative cross-backend contract and keep `property_method_call` and `list_bool_index` green in every target backend before close.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S1-01] Inventory the current repro bundle under `materials/refs/from-Pytra-NES2/` and lock the map of already-covered vs unresolved cases into the plan/docs.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S1-02] Promote `property_method_call.py` and `list_bool_index.py` into representative fixtures under `test/fixtures/`, with assertion-backed semantics.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-01] Add those fixtures to representative smoke for C++/C#/Rust/Go/Java/Kotlin/Scala/Swift/Nim and lock the C++ compile-failure baseline plus the static-family transpile smoke.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-02] Add those fixtures to representative smoke for JS/TS/Lua/Ruby/PHP and lock the script-family representative transpile contract.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S2-03] Add common assertion/helper/checker support as needed so `unsupported`, `preview_only`, or `not_implemented` counts as a failure.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S3-01] Make `property_method_call` green in every backend and sync docs / support wording / decision log.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S3-02] Make `list_bool_index` green in every backend and sync docs / support wording / decision log.
- [x] [ID: P0-PYTRA-NES2-CROSSBACKEND-REPRO-01-S4-01] Sync the final mapping between `materials/refs/from-Pytra-NES2` and repo fixtures/tests and close the bundle as fully promoted.

Decision log:
- 2026-03-13: Following the user instruction, the plan was changed from “close the two unresolved cases as C++ local bugfix tasks” to “add representative tests for all backends first, then fix implementations”.
- 2026-03-13: Current local inspection concluded that `bytes_truthiness`, `path_stringify`, and `field_default_factory_rc_obj` are already absorbed into existing fixture/smoke lanes, while `property_method_call` and `list_bool_index` remain unresolved.
- 2026-03-13: `path_alias_pkg/entry.py` is listed in the README but missing from the current bundle, so it remains out of scope until the file is actually present.
- 2026-03-13: `S1-01` locked a README-entry table covering current bundle presence, current repo status, representative-lane mapping, and the one missing-file case.
- 2026-03-13: `S1-02` added `test/fixtures/typing/property_method_call.py` and `test/fixtures/typing/list_bool_index.py`, locking the `@property` value-read/stringify semantics and the `list[bool]` read-write-reread semantics with assertions.
- 2026-03-13: `S2-01` wired `property_method_call` / `list_bool_index` into the current C++ compile-failure baseline plus representative transpile smoke for `cs/rs/go/java/kotlin/scala/swift/nim`. `property_method_call` currently fails because property reads leak as member-function references, and `list_bool_index` currently fails because `std::vector<bool>` proxy semantics collide with the `bool&` expectation.
- 2026-03-13: `S2-02` wired `property_method_call` / `list_bool_index` into representative transpile smoke for `js/ts/lua/ruby/php`, fixing Wave B at the transpile-contract level without allowing unsupported / preview escapes.
- 2026-03-13: `S2-03` added a shared denylist helper under `test/unit/backends/representative_contract_support.py` so every representative smoke fails if the emitted source contains `unsupported / preview_only / not_implemented` markers. The C++ current baselines now apply the helper to generated C++ source itself before checking the expected compile failure.
- 2026-03-13: `S3-01` added class-local `@property` getter tracking to the C++ emitter so attribute reads lower to `this->mapper()` / `holder->mapper()` instead of member-function objects. With that change, `property_method_call` is compile+run green on C++ too, so every backend representative lane is now green and only `list_bool_index` remains unresolved.
- 2026-03-13: `S3-02` switched the C++ runtime `list<T>` / `py_at` / `py_list_at_ref` surface to `list<T>::reference/const_reference` and added a bool-convertible proxy fallback to `make_object`. That removed the `std::vector<bool>` proxy vs `bool&` collision and made `list_bool_index` compile+run green on C++ too.
- 2026-03-13: `S4-01` synced the final mapping between `materials/refs/from-Pytra-NES2` and repo fixtures/tests. `bytes_truthiness` is covered by `test/fixtures/typing/bytes_truthiness.py` plus the archived representative lane, `path_stringify` by `test/fixtures/stdlib/path_stringify.py` plus its archived representative lane, `field_default_factory_rc_obj` by the archived dataclass representative lane, and `property_method_call` / `list_bool_index` by `test/fixtures/typing/*` plus representative smoke across every backend. `path_alias_pkg/entry.py` remains out of scope because the file is still absent from the bundle.
