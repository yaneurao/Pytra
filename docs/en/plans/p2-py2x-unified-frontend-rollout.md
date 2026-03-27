<a href="../../ja/plans/p2-py2x-unified-frontend-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Unified Frontend Rollout with `pytra-cli.py` (Layered Option Pass-through)

Last updated: 2026-03-02

Related TODO:
- `ID: P2-PY2X-UNIFIED-FRONTEND-01` in `docs/ja/todo/index.md`

Background:
- Currently, language-specific frontends (`py2cpp.py`, `py2cs.py`, `py2rs.py`, etc.) exist independently, with significant duplication in input handling, EAST3 conversion, CLI parsing, and output placement.
- Meanwhile, responsibility up to "input Python -> EAST3" is common, and backend differences should fundamentally live in `lower/optimizer/emitter/extensions`.
- User requirement: adopt a common interface that passes options from frontend by layer (`--lower-option`, `--optimizer-option`, `--emitter-option`).

Goal:
- Introduce `pytra-cli.py` as the shared frontend and consolidate language differences into a backend registry and layered option schemas.
- Gradually degrade existing `py2*.py` into compatibility wrappers and remove duplicated CLI/EAST3 preprocessing implementations.

Scope:
- New: `src/pytra-cli.py`
- New: backend registry (e.g., `src/pytra/compiler/backend_registry.py`)
- Update: existing `py2*.py` (thin-wrapper conversion)
- Update: docs (`how-to-use`, `spec-dev`, `spec-folder`, CLI examples)
- Update: transpile check tool set (verify `py2x` path)

Out of scope:
- Backend output quality improvements themselves (emitted content changes)
- EAST1/EAST2/EAST3 spec changes
- Immediate deletion of existing `py2*.py` (compatibility period remains)

Acceptance criteria:
- `pytra-cli.py --target <lang>` can dispatch existing supported languages (at least `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php`).
- `--lower-option`, `--optimizer-option`, and `--emitter-option` can transparently pass `key=value` pairs to backend layers.
- Layered options are validated by backend-side schemas; unknown keys/type errors fail-fast.
- Existing `py2*.py` preserve equivalent behavior while degrading to `py2x` invocations.
- Major transpile checks and unit tests pass without regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 src/pytra-cli.py --help`
- `python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp -o out/tmp_01.cpp`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`

## Breakdown

- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] Inventory CLI/runtime-placement differences in current `py2*.py` and finalize differences to keep in shared frontend conversion.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] Define shared CLI spec for `py2x` (`--target`, layered options, compatibility options, fail-fast rules).
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] Define backend registry contract (entrypoint, default options, option schema, runtime packaging hook).
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] Implement `pytra-cli.py` and introduce shared input handling (`.py/.json -> EAST3`) with target dispatch.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] Implement layered option parser (`--lower-option`, `--optimizer-option`, `--emitter-option`) and schema validation.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] Convert existing `py2*.py` into thin wrappers delegating compatible CLI to `py2x`.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] Move runtime/packaging differences to backend extension hooks and reduce frontend branching.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] Add CLI unit tests to lock target dispatch and layered option propagation.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] Run existing transpile checks through `py2x` path and verify cross-language non-regression.
- [x] [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] Update usage/spec docs in `docs/ja` / `docs/en` and document migration steps (including compatibility-wrapper period).

## S1-01 Inventory Results (2026-03-03)

### CLI differences

| Category | Target | Current state | Handling in `py2x` |
| --- | --- | --- | --- |
| Common CLI | `py2cs/rs/js/ts/go/java/kotlin/swift/rb/lua/php/scala/nim` | `INPUT`, `-o/--output`, `--parser-backend`, `--east-stage`, `--object-dispatch-mode`, EAST3 optimizer dump/level options | Integrate as common args in `py2x`. |
| C#-only custom implementation | `py2cs.py` | handwritten parser without `argparse` | Standardize with `argparse` in `py2x`; degrade `py2cs.py` into compatibility wrapper. |
| C++-specific CLI | `py2cpp.py` | `--single-file/--multi-file`, `--header-output`, `--emit-runtime-cpp`, `--output-dir`, C++/EAST3/CppOpt-specific option set | Do not add to common `py2x`; keep as backend options (`--lower/optimizer/emitter-option`) or in `py2cpp.py` compatibility wrapper. |
| Java-specific post-process | `py2java.py` | derives `class_name` from output filename | Handle in registry as backend extension hook (packaging hook). |

### Runtime placement differences

| Type | Target | Current state | Differences retained in `py2x` |
| --- | --- | --- | --- |
| No runtime bundling | `py2cs.py` | writes only output `.cs` | none |
| JS shim bundling | `py2js.py`, `py2ts.py` | calls `write_js_runtime_shims(output_dir)` | registry as `runtime_packaging_hook=js_shims` |
| Single runtime file bundling | `py2rs/go/java/kotlin/swift/rb/lua/scala/nim` | copies `py_runtime.*` (Java: `PyRuntime.java`) into same output directory | declare backend-specific `source/dest` as `runtime_packaging_hook=single_runtime_file` |
| Multi-file runtime bundling | `py2php.py` | copies `py_runtime.php`, `runtime/png.php`, `runtime/gif.php` under `pytra/` | registry as `runtime_packaging_hook=runtime_tree_copy` |
| Runtime generation mode present | `py2cpp.py` | generates `pytra-gen` from runtime modules via `--emit-runtime-cpp` | out of scope for initial `py2x` rollout (keep via `py2cpp.py` compatibility wrapper) |

### Differences retained in shared frontend conversion (fixed)

1. Consolidate input resolution (`.py/.json -> EAST3`), common guards, and common output writing in `py2x`.  
2. Delegate runtime placement to backend registry `runtime_packaging_hook`.  
3. Migrate large C++-specific CLI gradually; keep `py2cpp.py` compatibility wrapper in initial phase.  
4. Manage backend-specific post-process (e.g., Java `class_name` derivation) with backend extension hooks.  

## S1-02 Shared CLI Spec (2026-03-03)

### Basic form

```bash
python3 src/pytra-cli.py INPUT.py --target <lang> -o OUTPUT
```

- `--target` is required (initial support: `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim`).
- `INPUT` accepts `.py` or `.json` (EAST3 JSON).
- `-o/--output` remains explicitly recommended (unspecified behavior follows wrapper compatibility conventions).

### Common options

- `--parser-backend` (select EAST generation backend for `.py` input)
- `--east-stage` (only `3` is accepted; `2` fails fast)
- `--object-dispatch-mode` (`native|type_id`)
- Common EAST3 optimizer options:
  - `--east3-opt-level`
  - `--east3-opt-pass`
  - `--dump-east3-before-opt`
  - `--dump-east3-after-opt`
  - `--dump-east3-opt-trace`

### Layered option pass-through

- `--lower-option key=value` (can be repeated)
- `--optimizer-option key=value` (can be repeated)
- `--emitter-option key=value` (can be repeated)
- Accepted key/value pairs are validated by backend registry schema (defined in S1-03).

### Compatibility option policy

- Existing `py2*.py` remain as thin wrappers for now, mapping existing CLI into `py2x` and delegating.
- Large C++-specific CLI (`--single-file/--multi-file`, `--emit-runtime-cpp`, etc.) stays on wrapper side in initial phase and is migrated gradually.
- Backend-specific post-processes such as Java `class_name` derivation are moved to backend hooks, not frontend-specific branching.

### fail-fast rules

1. Missing `--target` or unknown target: immediate error.  
2. `--east-stage 2`: immediate error (compat mode removed).  
3. Invalid layered option format (not `key=value`): immediate error.  
4. Keys not in backend schema or values with type mismatch: immediate error.  
5. For `.json` input, specifying parser-related options is an explicit mismatch and must be an error (not warning/ignore).  

## S1-03 Backend Registry Contract (2026-03-03)

### Minimal registry entry contract

Each target must define the following in `BackendSpec` (tentative name).

1. `target: str`  
2. `lower_entry: Callable[[East3Module, LowerOptions], LangIRModule]`  
3. `optimizer_entry: Callable[[LangIRModule, OptimizerOptions], LangIRModule]`  
4. `emitter_entry: Callable[[LangIRModule, EmitterOptions], str]`  
5. `runtime_packaging_hook: Callable[[Path, RuntimePackagingOptions], None] | None`  
6. `default_options: {lower: dict, optimizer: dict, emitter: dict}`  
7. `option_schema: {lower: Schema, optimizer: Schema, emitter: Schema}`  
8. `compat_wrapper: list[str]` (corresponding legacy `py2*.py` names)

### Option schema contract

- Schemas are independent per layer and defined as `key -> {type, allowed, default, description}`.
- `py2x` validates `--*-option key=value` immediately; unknown keys and type mismatches fail fast.
- Schema defaults are reflected in `default_options`, guaranteeing the same resolution order even via wrappers.

### Runtime packaging hook contract

- Hook is called exactly once after `emit`, and may modify only inside output directory.
- Hook side effects are limited to runtime placement and must not modify generated source strings.
- At minimum, define the following hook types.
  - `none`
  - `js_shims`
  - `single_runtime_file`
  - `runtime_tree_copy`

### Compatibility wrapper contract

- Existing `py2*.py` perform only "arg interpretation -> mapping to `py2x` compatible args -> invoke `py2x`".
- Wrappers must not retain EAST3 generation or `lower/optimizer/emitter` execution.
- To preserve compatibility, backends in staged migration (e.g., C++) may temporarily keep options on wrapper side, but the final source of truth must be the registry path.

## S2-01 Implementation (2026-03-03)

- Added:
  - `src/pytra-cli.py`
  - `src/pytra/compiler/backend_registry.py`
- Implemented:
  - `py2x` receives `INPUT + --target` and builds EAST3 via `load_east3_document`.
  - Resolves and runs `lower -> optimizer -> emitter -> runtime_hook` from backend registry.
  - Supported targets: `cpp/rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/scala/php/nim`.
  - Explicitly supports `--help` (`-h/--help`) on `py2x` side.
- Constraints at implementation time:
  - Layered option parser / schema validation not yet implemented (handled in `S2-02`).
  - Existing `py2*.py` not yet delegated (thin-wrapper conversion in `S2-03`).
- Execution checks:
  - `python3 src/pytra-cli.py --help`
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target cpp -o /tmp/py2x_cpp.cpp`
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target rs -o /tmp/py2x_rs.rs`
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target php -o /tmp/py2x_php.php`
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target scala -o /tmp/py2x_scala.scala`

## S2-02 Implementation (2026-03-03)

- Added manual extraction of layered options in `pytra-cli.py`:
  - `--lower-option key=value`
  - `--optimizer-option key=value`
  - `--emitter-option key=value`
- Added schema resolver `resolve_layer_options(...)` in `backend_registry.py` and fail-fast checks for:
  - unknown keys
  - type mismatches (`int` / `bool` conversion failures)
  - values outside `choices`
- Current schema implementation:
  - `cpp.emitter`: `negative_index_mode`, `bounds_check_mode`, `floor_div_mode`, `mod_mode`
  - other backend/layer schemas are empty (specifying any key triggers unknown-key error)
- Execution checks:
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target cpp --emitter-option negative_index_mode=always --emitter-option bounds_check_mode=debug -o /tmp/py2x_cpp_opt.cpp`
  - `python3 src/pytra-cli.py sample/py/02_raytrace_spheres.py --target cpp --emitter-option unknown_key=1 -o /tmp/py2x_cpp_bad.cpp` (`exit=2` confirmed)

## S2-03 Implementation (2026-03-03)

- Added:
  - `src/pytra/compiler/py2x_wrapper.py`
- Implemented:
  - Switched existing frontend `main` into thin wrappers delegating to `run_py2x_for_target("<lang>")`.
  - Targets: `py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,php,scala,nim}.py`
  - `py2cs.py` keeps existing `main(argv)` call shape and delegates via `argv_override`.
  - Updated `tools/check_noncpp_east3_contract.py` for wrapper contract and made static checks accept both `legacy implementation` and `py2x thin wrapper`.
  - Added `pytra/std/time.php` copy in `py2x` PHP runtime hook to preserve existing contracts after `py2php` wrapper conversion.
- Execution checks:
  - `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
  - `python3 -m unittest discover -s test/unit -p test_east2_to_east3_lowering.py`
  - `python3 tools/check_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,php,scala,nim}_transpile.py`

## S2-04 Implementation (2026-03-03)

- Implemented:
  - Unified runtime/packaging in `backend_registry.runtime_hook`, and degraded non-C++ frontends to `run_py2x_for_target` only.
  - Added wrapper-oriented static guards to `tools/check_noncpp_east3_contract.py`, making reintroduction of legacy runtime-copy calls in `py2*.py` fail (e.g., `_copy_*_runtime(output_path)`, `write_js_runtime_shims(output_path.parent)`).
  - Included `pytra/std/time.php` in PHP runtime hook placement on `py2x` side to preserve legacy CLI contract.
- Execution checks:
  - `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
  - `python3 tools/check_py2php_transpile.py`

## S3-01 Implementation (2026-03-03)

- Added:
  - `test/unit/test_py2x_cli.py`
- Test coverage:
  - Locks fail-fast for missing `--target` (`SystemExit(2)`).
  - Locks rejection of `--east-stage 2` before entering backend pipeline.
  - Locks that `key=value` from `--lower-option/--optimizer-option/--emitter-option` propagates by layer to `resolve_layer_options`, and resolved results are passed to `lower_ir -> optimize_ir -> emit_source`.
  - Locks dispatch path through output write and `apply_runtime_hook` call.
- Execution checks:
  - `python3 -m unittest discover -s test/unit -p test_py2x_cli.py`

## S3-02 Implementation (2026-03-03)

- Implemented:
  - Ran all existing transpile checks through `py2x` path (`py2*.py` thin-wrapper route) and confirmed cross-language non-regression.
- Execution checks:
  - `python3 tools/check_py2cpp_transpile.py`
  - `python3 tools/check_py2rs_transpile.py`
  - `python3 tools/check_py2cs_transpile.py`
  - `python3 tools/check_py2js_transpile.py`
  - `python3 tools/check_py2ts_transpile.py`
  - `python3 tools/check_py2go_transpile.py`
  - `python3 tools/check_py2java_transpile.py`
  - `python3 tools/check_py2swift_transpile.py`
  - `python3 tools/check_py2kotlin_transpile.py`
  - `python3 tools/check_py2rb_transpile.py`
  - `python3 tools/check_py2lua_transpile.py`
  - `python3 tools/check_py2scala_transpile.py`
  - `python3 tools/check_py2php_transpile.py`
  - `python3 tools/check_py2nim_transpile.py`

## S3-03 Implementation (2026-03-03)

- Implemented:
  - Appended canonical `py2x` entrypoint and migration notes for `py2*.py` compatibility wrappers in `docs/ja/how-to-use.md` and `docs/en/how-to-use.md`.
  - Clarified the compatibility-wrapper period (compatibility guarantee/recommended path) and representative old->new command migration examples.

Decision log:
- 2026-03-02: Based on user direction, filed `pytra-cli.py` unification plan as P2 to remove duplication in language-specific frontends.
- 2026-03-02: Adopted layered pass-through (`--lower-option`, `--optimizer-option`, `--emitter-option`) as the canonical option model, with fail-fast backend schema validation.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-01] Inventoried CLI/runtime placement differences in `py2*.py` and finalized retained differences under unification as `runtime hook`, `backend post-process`, and `C++ compatibility-wrapper retention`.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-02] Finalized shared `py2x` CLI spec (basic form, common options, layered pass-through, compatibility policy, fail-fast rules).
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S1-03] Defined backend registry contract (entrypoint/default options/schema/runtime hook/compat wrapper) and fixed acceptance interface for S2 implementation.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-01] Implemented initial versions of `pytra-cli.py` and `backend_registry.py`, introducing shared EAST3 input handling + target dispatch + runtime-hook execution.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-02] Implemented layered option parser and schema validation in `py2x/backend_registry`, enabling fail-fast detection for unknown keys/invalid values.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-03] Completed staged delegation of non-C++ `py2*.py` to `run_py2x_for_target`, achieving thin wrappers while preserving compatibility CLI. Updated static contract checks to support both wrapper/legacy implementations, and restored transpile regression by filling a runtime-copy omission (`pytra/std/time.php`) in `py2php`.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S2-04] Fixed runtime/packaging responsibilities in `backend_registry.runtime_hook`, and blocked flow-back to frontend via wrapper static guards in `check_noncpp_east3_contract`.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-01] Added `test_py2x_cli.py` and locked target dispatch, stage2 fail-fast, and layered option propagation (`resolve_layer_options` path) with unit tests.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-02] Ran all `check_py2*_transpile.py` and confirmed non-regression of the `py2x` route even via thin wrappers.
- 2026-03-03: [ID: P2-PY2X-UNIFIED-FRONTEND-01-S3-03] Added migration notes for wrapper compatibility period in `docs/ja` / `docs/en` and documented migration steps to canonical `py2x` entrypoint.
