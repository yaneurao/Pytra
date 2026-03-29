<a href="../../ja/plans/p1-multilang-backend-3layer-realign.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Realign Non-C++ Backends into 3 Layers (`Lower` / `Optimizer` / `Emitter`)

Last updated: 2026-03-03

Related TODO:
- `ID: P1-MULTILANG-BACKEND-3LAYER-01` in `docs/ja/todo/index.md`

Background:
- The C++ backend has already moved to a three-layer structure (`lower/optimizer/emitter`), but non-C++ backends are still emitter-centric with mixed responsibilities.
- Placement of `hooks` / helpers / output support differs by language, increasing horizontal rollout cost for similar changes.
- Tasks such as generation-quality improvements, selfhost, and runtime separation tend to become per-language local optimizations because structure is inconsistent.

Goal:
- Gradually realign non-C++ backends into `Lower -> Optimizer -> Emitter` and standardize implementation responsibilities.
- Reduce `Emitter` to a final renderer; move semantic decisions and normalization into `Lower/Optimizer`.
- Establish a reusable migration template across backends (naming conventions, contracts, regression guards).

In scope:
- `src/toolchain/emit/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala}/`
- Each `py2*.py` bridge (minimal wiring changes only)
- Related unit/transpile checks/sample regeneration

Out of scope:
- Semantic-spec changes to EAST1/EAST2/EAST3
- Runtime API redesign per language
- Additional restructuring of C++ backend (handled in separate P0)

Acceptance criteria:
- Target backends have all three layer directories: `lower/optimizer/emitter`.
- Direct EAST3 semantic branching in `Emitter` is gradually reduced and migrated to `Lower/Optimizer`.
- Existing transpile checks / unit tests / sample regeneration remain non-regressive.
- Rule "new backends must be 3-layer" is reflected in `docs/ja/spec` and checks.

Implementation policy:
1. First fix common contracts (minimal IR contract, responsibility boundaries, naming rules).
2. Pilot migration on 1-2 languages and solidify migration templates.
3. Roll out the same template to remaining languages.
4. Add guards against old-structure relapse (old imports / semantic decisions flowing back into emitter).

Recommended migration order:
- Wave 1: `rs`, `scala` (already relatively mature in quality and type utilization)
- Wave 2: `js`, `ts`, `cs`
- Wave 3: `go`, `java`, `kotlin`, `swift`
- Wave 4: `ruby`, `lua`, `php` (with runtime/support-layer differences)

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `python3 tools/check/check_py2scala_transpile.py`
- `python3 tools/check/check_py2js_transpile.py`
- `python3 tools/check/check_py2ts_transpile.py`
- `python3 tools/check/check_py2cs_transpile.py`
- `python3 tools/check/check_py2go_transpile.py`
- `python3 tools/check/check_py2java_transpile.py`
- `python3 tools/check/check_py2kotlin_transpile.py`
- `python3 tools/check/check_py2swift_transpile.py`
- `python3 tools/check/check_py2rb_transpile.py`
- `python3 tools/check/check_py2lua_transpile.py`
- `python3 tools/check/check_py2php_transpile.py`

## Breakdown

- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] Create an inventory of current responsibility placement in non-C++ backends (where semantics/normalization/rendering are done).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] Define a 3-layer contract (minimal LangIR contract, fail-closed on failure, per-layer prohibitions).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] Document directory/naming rules (`lower/*`, `optimizer/*`, `emitter/*`) and import rules.
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Introduce `lower/optimizer` skeletons for Wave 1 (`rs`) and switch `py2rs` to 3-layer wiring.
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Introduce `lower/optimizer` skeletons for Wave 1 (`scala`) and switch `py2scala` to 3-layer wiring.
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Fix Wave 1 regressions (unit/transpile/sample) and finalize migration templates.
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Roll out the same template to Wave 2 (`js/ts/cs`).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Roll out the same template to Wave 3 (`go/java/kotlin/swift`).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Roll out the same template to Wave 4 (`ruby/lua/php`).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] Add checks preventing old-structure relapse (old imports / emitter responsibility backflow).
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] Update `docs/ja/spec` / `docs/en/spec` to formalize 3 layers as backend standard structure.

## S1-01 Inventory Results (2026-03-03)

| backend | Current structure | Main location of semantic decisions/normalization | Main rendering location | Notes |
| --- | --- | --- | --- | --- |
| `rs` | `emitter/rs_emitter.py` + `hooks/rs_hooks.py` | `rs_emitter.py` (many `kind ==` branches, `ForCore` expansion) | `rs_emitter.py` | Inherits `CodeEmitter`. Runtime import/support function generation also mixed in. |
| `cs` | `emitter/cs_emitter.py` + `hooks/cs_hooks.py` | `cs_emitter.py` (type checks, `isinstance` lowering, range expansion) | `cs_emitter.py` | Inherits `CodeEmitter`. Runtime-call selection concentrated in emitter. |
| `js` | `emitter/js_emitter.py` + `hooks/js_hooks.py` | `js_emitter.py` (includes import/runtime symbol collection) | `js_emitter.py` | Inherits `CodeEmitter`. Strong mix of semantic decisions and rendering. |
| `ts` | `emitter/ts_emitter.py` | Mostly delegated to `js` | Thin wrapper around `js` output | No TS-specific Lower/Optimizer yet. |
| `go` | `emitter/go_native_emitter.py` | `go_native_emitter.py` (`ForCore` / compare / call lowering) | `go_native_emitter.py` | Consolidated in one native emitter. |
| `java` | `emitter/java_native_emitter.py` | `java_native_emitter.py` | `java_native_emitter.py` | Single native emitter. |
| `kotlin` | `emitter/kotlin_native_emitter.py` | `kotlin_native_emitter.py` | `kotlin_native_emitter.py` | Single native emitter. |
| `swift` | `emitter/swift_native_emitter.py` | `swift_native_emitter.py` | `swift_native_emitter.py` | Single native emitter. |
| `ruby` | `emitter/ruby_native_emitter.py` | `ruby_native_emitter.py` | `ruby_native_emitter.py` | Single native emitter. |
| `lua` | `emitter/lua_native_emitter.py` | `lua_native_emitter.py` | `lua_native_emitter.py` | Single native emitter. |
| `scala` | `emitter/scala_native_emitter.py` | `scala_native_emitter.py` | `scala_native_emitter.py` | Single native emitter. |
| `php` | `emitter/php_native_emitter.py` | `php_native_emitter.py` (contains dict/in/ctor/entrypoint lowering) | `php_native_emitter.py` | Single native emitter. |
| `nim` | `emitter/nim_native_emitter.py` | `nim_native_emitter.py` | `nim_native_emitter.py` | Newly introduced backend; include in 3-layerization from the start. |

Inventory summary:
- All non-C++ backends are effectively single-layer emitters with mixed semantic decisions, normalization, and rendering.
- `rs/cs/js` use `CodeEmitter` inheritance + hooks, but have not reached Lower/Optimizer separation.
- `go/java/kotlin/swift/ruby/lua/scala/php/nim` are single native emitters with no prepared path for 3-layerization.

## S1-02 3-Layer Contract (2026-03-03)

### Lower contract
- Input: EAST3 Module.
- Output: LangIR Module (language-specific but semantic-preserving, no text generation).
- Responsibility: Normalize language-required decisions (range expansion, membership strategy, entrypoint shape) into LangIR nodes.
- Prohibited: Direct source generation by string concatenation, runtime file placement, I/O.

### Optimizer contract
- Input/output: LangIR Module -> LangIR Module.
- Responsibility: Semantic-preserving local transforms (remove redundant casts, simplify, assist dependency collection).
- Prohibited: Reinterpret EAST, text generation, side-effectful optimization.

### Emitter contract
- Input: LangIR Module.
- Output: language source string.
- Responsibility: formatting, lexical shaping, final rendering.
- Prohibited: New semantic decisions (for example choosing `in/not in` evaluation strategy), re-inference of type resolution.

### fail-closed rules
- Lower/Optimizer/Emitter must return `RuntimeError` for unknown nodes/attributes instead of silently skipping.
- Implicit fallback across layer boundaries is prohibited (example: emitter rescans EAST3 directly for patching).
- CI does not allow `check_py2<lang>_transpile` failures (known failures must be tracked in explicit lists).

## S1-03 Naming and Import Rules (2026-03-03)

Directory rules:
- `src/toolchain/emit/<lang>/lower/`:
  - `ir.py` (LangIR node definitions)
  - `from_east3.py` (EAST3 -> LangIR)
- `src/toolchain/emit/<lang>/optimizer/`:
  - `pipeline.py` (pass composition)
  - `passes/*.py` (individual optimizations)
- `src/toolchain/emit/<lang>/emitter/`:
  - `<lang>_emitter.py` or `<lang>_native_emitter.py` (LangIR -> text)
  - Rendering helpers such as `runtime_paths.py` / `profile_loader.py`

Import rules:
- `py2<lang>.py` may reference only in order: `toolchain.emit.<lang>.lower` -> `optimizer` -> `emitter`.
- `emitter` must not import `lower` directly (cycle dependency prohibited).
- Direct dependency across language backends is prohibited (example: a structure where `ts` delegates to `js` emitter internals is a staged-removal target).
- If sharing is needed, extract to and reference common layers under `pytra/compiler/*`.

Migration unit:
- Finalize the rules template in Wave 1 (`rs`, `scala`), then apply the same template in Wave 2+.

Decision log:
- 2026-03-02: Per user instruction, opened P1 for "unify non-C++ backends to `Lower/Optimizer/Emitter`".
- 2026-03-02: Adopted a Wave model (2-language pilot -> horizontal rollout) instead of all-at-once migration.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] Completed inventory of current responsibilities in non-C++ backends and documented mixed-responsibility points.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] Finalized Lower/Optimizer/Emitter contracts and fail-closed rules.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] Finalized directory naming/import rules and recorded Wave 1 template policy.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Introduced `toolchain/emit/rs/lower` and `toolchain/emit/rs/optimizer`; switched `py2rs.py` to 3-layer wiring. `check_py2rs_transpile` passed.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Introduced `toolchain/emit/scala/lower` and `toolchain/emit/scala/optimizer`; switched `py2scala.py` to 3-layer wiring. `check_py2scala_transpile` (`checked=141 ok=141 fail=0`) passed.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] First Wave 1 regression run showed `SUMMARY cases=18 pass=6 fail=12` (`scala` `run_failed=12`); main causes were `__pytra_bytearray/__pytra_bytes` return-type mismatch and invalid normalization in `ForCore` conditions (`value` contamination).
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Fixed `bytearray/bytes` in `src/runtime/scala/pytra/py_runtime.scala` to return `ArrayBuffer[Long]`, and added identifier-validation fallback for normalized conditional expressions in `scala_native_emitter`. Passed `check_py2scala_transpile` (141/141), `check_py2rs_transpile` (131/131, skipped=10), and `runtime_parity_check --case-root sample --targets rs,scala --ignore-unstable-stdout` (18/18).
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Added `lower` and `optimizer` to `toolchain/emit/{js,ts,cs}` and switched `py2{js,ts,cs}.py` to `lower -> optimizer -> emitter` wiring. `check_py2{js,ts,cs}_transpile` passed with `checked=133 ok=133 fail=0 skipped=8` each.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave 2 sample parity (`runtime_parity_check --case-root sample --targets js,ts,cs --ignore-unstable-stdout`) showed `cases=18 pass=14 fail=4`, `artifact_size_mismatch=8` (`js/ts` `01-04`). No transpile breakage caused by 3-layer wiring changes; artifact differences were carried over as known issues to the next wave.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Added `lower` and `optimizer` to `toolchain/emit/{go,java,kotlin,swift}` and switched `py2{go,java,kotlin,swift}.py` to `lower -> optimizer -> emitter` wiring. `check_py2{go,java,kotlin,swift}_transpile` passed with `checked=131 ok=131 fail=0 skipped=10` each.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave 3 sample parity (`runtime_parity_check --case-root sample --targets go,java,kotlin,swift --ignore-unstable-stdout`) showed `cases=18 pass=1 fail=17` (`go: run_failed=11`, `java: run_failed=5 + artifact_missing=12`, `swift: toolchain_missing=18`, `kotlin: no failures`). Transpile checks confirmed no regression from 3-layer wiring changes; execution-level gaps remain tracked as wave-specific issues.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Added `lower` and `optimizer` to `toolchain/emit/{ruby,lua,php}` and switched `py2{rb,lua,php}.py` to `lower -> optimizer -> emitter` wiring. Passed `check_py2rb_transpile` (`checked=132 ok=132 fail=0 skipped=10`), `check_py2lua_transpile` (`checked=89 ok=89 fail=0 skipped=53`), and `check_py2php_transpile` (`checked=10 ok=10 fail=0 skipped=0`).
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave 4 sample parity (`runtime_parity_check --case-root sample --targets ruby,lua,php --ignore-unstable-stdout`) showed `cases=18 pass=14 fail=4`. Breakdown: for `php`, `output_mismatch=2` (`12/13`) and `run_failed=1` (`16`); for `ruby`, `run_failed=1` (`18`); `lua` had no failures. Transpile regression from 3-layer wiring changes was already confirmed non-regressive.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] Expanded `tools/check/check_noncpp_east3_contract.py` to 12 backends (`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/php/scala`), adding static checks for required `lower/optimizer` wiring patterns/order in `py2<lang>.py` and banning reverse imports between `lower/optimizer` and `emitter`. Both `python3 tools/check/check_noncpp_east3_contract.py --skip-transpile` and `python3 tools/check/check_noncpp_east3_contract.py` (with 12 transpile checks) passed.
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] Updated `docs/ja/spec/{spec-dev,spec-folder}.md` and `docs/en/spec/{spec-dev,spec-folder}.md` to formalize non-C++ backend 3-layer standards (applicable backends, layer responsibilities, reverse-flow prohibition, check path). This completes all breakdown tasks for `P1-MULTILANG-BACKEND-3LAYER-01`.
