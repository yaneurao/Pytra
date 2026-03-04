# P2: Align Multi-language Runtime with C++ (Unified API Contracts and Feature Coverage)

Last updated: 2026-03-02

Related TODO:
- `ID: P2-RUNTIME-PARITY-CPP-01` in `docs/ja/todo/index.md`

Background:
- C++ runtime splits functionality into `built_in/std/utils`, and has relatively broad coverage up to `math/time/json/pathlib/random/re/sys/...`.
- Many other language runtimes are centered on a single `py_runtime`, and have not reached C++-equivalent API/feature coverage.
- Existing P1 (runtime extraction) targets "inline helper removal" and does not guarantee C++-equivalent functionality.

Goal:
- Treat C++ runtime as the canonical specification and incrementally align API contracts and feature coverage in other language runtimes.
- Build adapter layers that absorb backend differences so generated code can call equivalent APIs without language-specific awareness.

Scope:
- `src/runtime/{cs,go,java,js,ts,kotlin,swift,ruby,lua,scala,php,rs}/`
- Runtime call surfaces in `src/backends/<lang>/emitter/*` as needed
- Parity verification scripts and runtime contract tests

Out of scope:
- Large redesign of C++ runtime itself
- EAST spec changes
- Full one-shot port of all standard libraries (staged rollout)

Acceptance criteria:
- Availability of implementations in each language runtime is listed against the C++ runtime "required API set".
- At least the common API baseline (`math/time/pathlib/json/png/gif` + core helpers) satisfies equivalent contracts per language via same-name APIs or adapters.
- Runtime-difference-originated fails in `sample`/`test` parity checks can be reduced incrementally.
- Regression checks are added to track runtime differences (missing API detection).

Execution policy:
1. Finalize a "required API catalog" based on C++ runtime.
2. Create implementation maps for each language runtime and classify gaps/behavior differences.
3. Fill high-gap areas first (`math/time/pathlib/json`, etc.).
4. Move emitter-side language-specific calls to adapters and reduce API naming variance.
5. Lock parity/regressions for each feature addition.

Recommended rollout order:
- Wave 1: `go/java/kotlin/swift` (strong single-runtime dependence; high impact from gap absorption)
- Wave 2: `ruby/lua/scala/php`
- Wave 3: `js/ts/cs/rs` (implementations are relatively advanced; fill remaining holes)

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`
- language-specific `check_py2*.py` (target backends)

## Breakdown

- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] Extract required C++ runtime API catalog (module/function/contract) and create canonical list.
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] Build implementation-presence matrix for each language runtime and classify missing/compatible/behavior-diff.
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] Prioritize parity targets in three tiers: `Must/Should/Optional`.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Implement/unify missing `math/time/pathlib/json` APIs in Wave1 (`go/java/kotlin/swift`).
- [x] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Wave1-Go: add `json.loads/dumps` runtime API and unify Go emitter `json.*` calls to runtime helpers.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Shift Wave1 emitter calls through adapters and absorb API naming variance.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Add Wave1 parity regressions and lock runtime-difference-originated fails.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Implement/unify missing APIs similarly in Wave2 (`ruby/lua/scala/php`).
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Shift Wave2 emitter calls through adapters.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Add Wave2 parity regressions and lock runtime-difference-originated fails.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Fill missing APIs and resolve contract differences in Wave3 (`js/ts/cs/rs`).
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] Add missing runtime API detection checks and integrate into CI/local regressions.
- [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] Reflect runtime-parity policy and progress table in `docs/ja/spec` / `docs/en/spec`.

Decision log:
- 2026-03-02: Based on user request, filed a P2 plan targeting "C++-equivalent functionality" as a separate axis from runtime extraction (P1).
- 2026-03-02: Adopted "API contract/behavior parity" as completion criteria instead of "matching implementation line counts."
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] Added C++ runtime canonical catalog (core/math/time/pathlib/json/png/gif + timeit/random) to `docs/ja/spec/spec-runtime.md`, fixing Wave baseline APIs.
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] Inventoried `src/runtime/<lang>/pytra`, finalized implementation-presence matrix (`native/mono/compat/missing`) and major gaps (`json/pathlib/gif/separation-layout differences`).
- 2026-03-03: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] Prioritized matrix results into `Must/Should/Optional` and fixed implementation order for Wave1/2/3.
- 2026-03-04: [ID: P2-RUNTIME-PARITY-CPP-01-S2-01-S1-01] Implemented `pyJsonLoads/pyJsonDumps` in Go runtime (`encoding/json` + number-preserving decode), and mapped `json.loads/json.dumps` in Go emitter to runtime helpers. Confirmed pass on `test_py2go_smoke.py` and `check_py2go_transpile.py`.

## S1-01 Implementation (2026-03-03)

- Reflected in: section "0. C++ Runtime API Canonical Catalog" in `docs/ja/spec/spec-runtime.md`.
- Extraction result:
  - `Must`: `built_in/core`, `std/math`, `std/time`, `std/pathlib::Path`, `std/json`, `utils/png`, `utils/gif`
  - `Should`: `std/timeit`, `std/random`
- Fixed canonical paths as `pytra-core` / `pytra-gen`, and documented `pytra/*` as forwarder layers.

## S1-02 Implementation (2026-03-03)

Classification keys:
- `native`: separately implemented as dedicated module/namespace
- `mono`: implemented inside a single `py_runtime.*`
- `compat`: directly tied to language standard API (no dedicated runtime API)
- `missing`: implementation not confirmed (may be missing/alternative behavior when called)

| lang | core helper | math | time | pathlib | json | png | gif | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cs` | mono | native | native | native | native | native | native | Closest separated layout to C++ baseline. |
| `js` | mono | native | native | native | compat | native | native | No dedicated runtime for `json` (depends on JS `JSON.*`). |
| `ts` | mono | native | native | native | compat | native | native | Same family as JS. |
| `go` | mono | mono | mono | mono | missing | mono | mono | Concentrated into single `py_runtime.go`. |
| `java` | mono | mono | mono | mono | missing | mono | mono | Concentrated into single `PyRuntime.java`. |
| `kotlin` | mono | missing | mono | missing | missing | mono | missing | For image, only PNG confirmed. |
| `swift` | mono | missing | mono | missing | missing | mono | missing | For image, only PNG confirmed. |
| `ruby` | mono | missing | mono | missing | missing | mono | mono | Single `py_runtime.rb`. |
| `lua` | mono | mono | mono | mono | missing | mono | mono | path/gif/png are monolithic helpers. |
| `scala` | mono | compat | mono | mono | missing | mono | mono | Math mainly uses language standard APIs. |
| `php` | mono | missing | native | missing | compat | native | native | Uses `json_encode` but lacks `loads/dumps` contract. |
| `rs` | mono | mono | mono | mono | missing | mono | mono | Consolidated in `built_in/py_runtime.rs`. |
| `nim` | mono | missing | mono | missing | missing | mono | missing | Currently minimal runtime. |

Primary classes of missing/compat/behavior differences:
1. `json` missing: same-name APIs matching C++ `loads/dumps` are missing outside `cs` (`js/ts/php` are compat paths using standard APIs).
2. `pathlib` missing: `kotlin/swift/ruby/php/nim` have not reached minimal C++ `Path` API set.
3. Uneven image API coverage: `gif` side missing in `kotlin/swift/nim` (only `png`).
4. Implementation-shape difference: `go/java/rs/lua/scala/ruby` concentrate in monolithic runtimes and diverge from separated layout in `cs/js/ts`.

## S1-03 Implementation (2026-03-03)

### Must (Wave1/2 first)

1. Add `json.loads/dumps` to `go/java/kotlin/swift/ruby/lua/scala/php/rs/nim` and align to C++ public contract.
2. Add minimal `pathlib.Path` APIs (`resolve/parent/name/stem/exists/mkdir/read_text/write_text`) to `kotlin/swift/ruby/php/nim`.
3. Add `gif` APIs (`grayscale_palette/save_gif`) to `kotlin/swift/nim`.
4. Route emitter calls for `math/time/pathlib/json/png/gif` through adapters to absorb naming variance.

### Should (Wave2/3)

1. Gradually migrate monolithic implementations (`go/java/rs/lua/scala/ruby`) to separated `std/*` / `utils/*` layout.
2. Fill missing C++-equivalent `timeit/random` APIs in lacking languages.
3. Align `json` compat paths in `js/ts/php` to dedicated runtime API names.

### Optional (later)

1. Tighten behavior differences after API name alignment (exception text / tolerance bands).
2. Optimize runtime placement after module separation (responsibility cleanup aligned with `profiles`).
3. Add automatic runtime-missing diagnostics in `tools/` for parity failures.
