<a href="../ja/changelog.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Changelog

## 2026-03-31

- **Ruby / Lua / PHP / Nim backend teams added**: TODO and plans created for each language.
- **C# / Java emitter progress**: C# strings 12/12 PASS, Java S1/S2 complete.
- **spec-python-compat: bool is NOT a subtype of int**: isinstance(True, int) returns False in Pytra.
- **spec-emitter-guide §15 FAQ expanded**: unsigned right shift, package manager prohibition, type check skip prohibition, yields_dynamic cast guidance.
- **EAST3 narrowing Cast node**: Rust team implemented Cast node insertion after isinstance narrowing.
- **P7-GO-SELFHOST-RUNTIME filed**: 3 gaps identified for Go selfhost binary.
- **Dockerfile: add TypeScript compiler**: `npm install -g typescript`. Removed package.json/node_modules.
- **parity check: npx tsx → tsc + node**: Zero npm dependency.

## 2026-03-30

- **Go fixture all PASS**: Container types unified to reference wrappers. All 147 fixtures + stdlib 16/16 PASS.
- **Rust emitter fixture 132/132 PASS**: arg_usage mut control, narrowing workaround.
- **TypeScript emitter S5-S7 complete**: fixture 146/146, sample 18/18, JS 147/147 PASS. ESM migration, PNG encoder transpiled.
- **C++ emitter P3-CR-CPP all complete**: S1-S8. isinstance unification, rc_from_value, keyword escaping.
- **Fast parity check**: In-memory toolchain2 API calls. `--category` option.
- **Automatic parity result accumulation + progress page**: 5 matrices (fixture/sample/stdlib/selfhost/emitter lint) + summary, auto-generated in ja+en.
- **stdlib test separation**: Per-module tests in `test/stdlib/source/py/<module>/`. `--case-root stdlib` added.
- **mapping.json types table**: Type mapping unified in mapping.json. `CodeEmitter.resolve_type()` API.
- **Emitter hardcode lint**: 7-category grep-based violation detection.
- **TODO per-area split**: cpp/go/rust/ts/cs/java/infra. P0 blocker rule removed.
- **Golden files untracked**: ~400MB JSON removed from git. Regenerate with `regenerate_golden.py`.
- **spec-runtime-decorator expansion**: extern_var, pipeline flow, quick reference table.
- **Sample benchmark auto-measurement**: elapsed_sec recorded, sample README auto-updated.
- **integer_promotion fixture**: All integer type widening/sign extension/mixed arithmetic tests.
- **pytra.std.env added**: env.target compile-time constant via mapping.json.
- **gc_reassign fixture fix**: __del__ body changed to pass (no GC-timing stdout).

## 2026-03-29

- **Go fixture all PASS**: Unified Go emitter container types to reference wrappers (`*PyList[T]`, `*PyDict[K,V]`, `*PySet[T]`) (P1-GO-CONTAINER-WRAPPER S1-S3). All 147 fixtures + stdlib 16/16 PASS.
- **Rust emitter new implementation (P7-RS-EMITTER)**: New Rust emitter in `src/toolchain2/emit/rs/` with CommonRenderer + override architecture. mapping.json created. Fixture emit success.
- **TypeScript emitter new implementation (P8-TS-EMITTER)**: New TS emitter in `src/toolchain2/emit/ts/`. JS covered by type annotation stripping flag on the same emitter. mapping.json created. 142 fixtures emit success.
- **C++ emitter parity improvements (P3-CR-CPP)**: Reserved word escaping (`_safe_cpp_ident`), optional dict.get, float/container printing fixes. oop 18/18, typing 22/22, signature 13/13 PASS.
- **C++ runtime exception safety (P3-CR-CPP-S4)**: Rewrote 5 `Object<void>` constructors in py_types.h to use `make_unique` + `release` pattern.
- **Fast parity check**: New `runtime_parity_check_fast.py` using in-memory toolchain2 API calls for transpile stage, eliminating subprocess startup and disk I/O.
- **`--category` option for runtime_parity_check**: Run parity checks per fixture subdirectory (oop, control, typing, etc.) instead of all 146+ cases.
- **Automatic parity result accumulation + progress page (P5-BACKEND-PROGRESS)**: Parity check auto-writes to `.parity-results/` with per-case merge and timestamps. `tools/gen/gen_backend_progress.py` generates fixture/sample/selfhost matrices in both Japanese and English.
- **mapping.json validator (P10.5-MAPPING-VALIDATE)**: New `tools/check/check_mapping_json.py` validating required entries (`env.target`), format, and structure for all languages. Integrated into `run_local_ci.py`.
- **spec-runtime-decorator expansion**: Added `extern_var` section, pipeline resolution flow (parser → resolve → emitter responsibilities), quick reference table.
- **spec-emitter-guide expansion**: §1.4 generated code quality (exception safety, reserved word escaping, generic `rc_from_value<T>`), §7.1-7.3 mapping.json constant substitution, literal embedding, mandatory `env.target`.
- **spec-tools reorganization**: Split into index + 3 detail pages (daily, parity, update-rules). Removed 7 unregistered tools.
- **TODO per-area split**: Reduced `todo/index.md` to index only, split into `cpp.md` / `go.md` / `rust.md` / `ts.md` / `infra.md`. Each agent reads/writes only its own area file. Removed P0 global blocker rule.
- **Legacy `@abi` reference cleanup**: Removed `@abi` / `runtime_abi_v1` from spec-east, spec-dev, spec-runtime, guide, and tutorial. Unified to `@runtime` / `@extern`.
- **PNG fixture path fix**: Changed output from `out/` to `test_png_out/` with `os.makedirs`. Fixes parity check cwd mismatch.

## 2026-03-28

- **Go exception handling completed (P0-EXCEPTION-GO)**: Typed catch, accurate catch/rethrow for custom exceptions, `raise ... from ...`, bare rethrow, and union-return vertical slice implemented. Builtin exceptions consolidated into `pytra.built_in.error`.
- **C++ native exception lowering (P0-EXCEPTION-CPP)**: Native exception lowering implemented for the C++ backend.
- **Go selfhost progress (P2-SELFHOST)**: Lowering profile support, reference wrapper default for container locals, `yields_dynamic`-based type assertion, Go mapping dispatch + parity coverage completed. P2-LOWERING-PROFILE-GO completed.
- **CommonRenderer extensions**: elif chain rendering moved to common renderer. C++ common renderer parity regressions fixed.
- **type_id table linker generation (P0-TYPE-ID-TABLE)**: Spec and implementation for linker-generated `pytra.built_in.type_id_table`. Hardcoded type_id deprecation policy finalized.
- **@runtime / @extern decorator design completed (P0-RUNTIME-DECORATOR)**: Unified to `@runtime("namespace")` + `@extern` + `runtime_var("namespace")`. Auto-derivation rules, `symbol=` / `tag=` optional overrides, and include file structure specified in spec-runtime-decorator.md. Legacy `@extern_method` / `@abi` abolished.
- **P0-CPP-INCLUDE-PATH-FIX**: Fixed runtime include path inconsistency in C++ emitter.
- **P0-GO-PATHLIB-FIX**: Fixed Go emitter pathlib signature issues (joinpath vararg, read_text/write_text).
- **Spec restructuring**: 12 legacy specs archived. spec-codex.md renamed to spec-agent.md. spec/index.md reorganized into categorized tables. 6 previously unlinked specs added. spec-opaque-type.md (`@extern class` type contract) created.
- **Guide section added**: 5 guide pages (EAST, emitter, type system, runtime, extern/FFI) added to docs/guide/. Guide section positioned between Tutorial and Specification.
- **Tutorial expansion**: Exception handling, Python differences, module reference (argparse/glob/re/enum/timeit), and samples pages added. Reading order restructured.
- **AGENTS.md split**: Separated into planner / coder role-specific specs. Minimized bootstrap entry.

## 2026-03-27

- **C++ emitter spec compliance (S1-S15)**: Fail-fast, mapping.json unification, container reference wrappers (`Object<list<T>>` etc.), implicit_promotions, is_entry/main_guard_body, @property support, shared runtime path resolution.
- **Traits (pure interface, multiple implementation)**: `@trait` / `@implements` decorators for pure interfaces. C++ uses virtual inheritance + `Object<T>` converting constructor; Go uses interface generation. Trait isinstance is compile-time only (no runtime info needed).
- **isinstance narrowing**: Automatic type environment update after `if isinstance(x, T):` in the resolve stage. Supports if/elif, early return guard (`if not isinstance: return`), ternary isinstance (`y = x if isinstance(x, T) else None`), and `and`-chained conditions.
- **Ternary Optional type inference**: `expr if cond else None` → `Optional[T]`, different types → `UnionType` inferred at resolve.
- **pytra.std.json parser support**: PEP 695 recursive type alias (`type JsonVal = ...`) and Union forward reference now parseable. Golden files regenerated.
- **POD isinstance**: `isinstance(x, int16)` etc. implemented as exact type match. Specified in spec-type_id.md §4.2.
- **Link input completeness check**: Unresolved imports in link-input are reported as fail-closed errors. Type stubs for unparseable modules.
- **ClosureDef lowering**: Nested FunctionDef lowered to ClosureDef in EAST3 with capture analysis (readonly/mutable).
- **Lowering profile design**: Language capability declarations (tuple_unpack_style, container_covariance, with_style, etc. — 16 items) added to spec-language-profile.md §7. CommonRenderer design in §8.
- **Tutorial additions**: Union types and isinstance narrowing, Traits tutorial pages added. English translations included.

## 2026-03-26

- **Pipeline redesign completed**: All 6 stages of the pipeline (`parse → resolve → compile → optimize → link → emit`) via `pytra-cli2` are fully operational. toolchain2 is a completely independent implementation with no dependency on toolchain.
- **Go backend migrated to new pipeline**: Go emitter + runtime implemented on the new pipeline. 18/18 samples emit success. Legacy Go emitter/runtime removed.
- **C++ emitter new implementation**: New pipeline C++ emitter implemented in `toolchain2/emit/cpp/`. fixture 132/132, sample 18/18 emit success.
- **CodeEmitter base class**: runtime_call mapping via `mapping.json` shared across all emitters. Hardcoding removed.
- **Spec conformance (Codex-review)**: 20+ spec violations fixed across resolve/parser/validator/linker/emitter.
- **spec-east1.md / spec-east2.md**: EAST1 (type-unresolved) and EAST2 (type-determined) output contracts formally defined.
- **spec-builtin-functions.md**: Built-in function declaration spec. POD/Obj type classification, dunder delegation, extern_fn/extern_var/extern_class/extern_method.
- **spec-runtime-mapping.md**: mapping.json format spec. implicit_promotions table.
- **Integer promotion**: Numeric promotion casts conforming to C++ usual arithmetic conversion inserted at resolve.
- **bytearray support**: `pytra/utils/png.py` / `gif.py` rewritten from `list[int]` to `bytearray`. Maps to `[]byte` in Go.

## 2026-03-25

- **All P0 tasks completed**: All stages (parse/resolve/compile/optimize/link/emit) match golden file tests.
- **test/ directory reorganization**: Organized into 5 categories: fixture/sample/include/pytra/selfhost.
- **Automatic golden file regeneration**: `tools/gen/regenerate_golden.py` for batch regeneration of all golden files.
- **Go emitter**: Implemented as the reference emitter. fixture 132/132, sample 18/18 emit success.
- **Go runtime + parity**: 18/18 samples pass `go run` + stdout match. Go is 63x faster than Python.
- **Go runtime decomposition**: Split `pytra_runtime.go` monolith into `built_in/` + `std/` + `utils/`.

## 2026-03-24

- **Pipeline redesign started**: Designed 5-stage pipeline (parse/resolve/compile/optimize/emit), later expanded to 6 stages with link.
- **toolchain2/ created**: New pipeline implementation independent of existing toolchain/. Selfhost-ready (no Any/object, pytra.std only).
- **pytra-cli2**: New CLI with -parse/-resolve/-compile/-optimize/-link/-emit/-build subcommands.
- **EAST1 golden files**: Golden files stripped (type info removed) conforming to spec-east1. 150 files.
- **Built-in function declarations**: `src/include/py/pytra/built_in/builtins.py` + `containers.py`. v2 extern (extern_fn/extern_var/extern_class/extern_method).
- **stdlib declarations**: v2 extern declarations for math/time/glob/os/sys etc. in `src/include/py/pytra/std/`.

## 2026-03-23

- Dart emitter dead code removal (14 functions deleted). Runtime helper dedup. 18/18 parity.
- Nim emitter spec-emitter-guide compliance improvements. Introduced `build_import_alias_map`, `yields_dynamic` support.
- Common test suite for all backends. `runtime_parity_check.py` enables fixture 131 execution across all languages.
- EAST3 type inference bug fixes x4 (reported by Nim: Swap, returns, VarDecl, list[unknown]).
- ContainerValueLocalHintPass generalized to all backends.
- Swap node constrained to Name-only, Subscript swap expanded to Assign.
- `unused: true` added to `_` elements in tuple destructuring.
- cast() resolved_type fix + list.pop() generic resolution.
- C++ multi-file emit runtime east path resolution fix.
- C++ test_py2cpp_features.py pass rate 64% → 95%.

## 2026-03-22

- REPO_ROOT fix + import alias resolution + conftest extern function fix.
- `build_multi_cpp.py` generated source changed to include-tracking-based auto-linking.
- Object<T> migration phases 1–4 completed (ControlBlock, emitter, list/dict, legacy type removal).

## 2026-03-21

- Removed `noncpp_runtime_call` / `noncpp_module_id` from EAST1 parser (resolving EAST1 responsibility violation).
- Decomposed py_runtime.h into 6 files with facade pattern.
- Runtime .east auto-integrated into link pipeline.
- Unified object = tagged value. Tagged union unified to PyTaggedValue (object+tag).
- Removed all legacy object APIs (make_object, obj_to_rc_or_raise, etc.).
- Escape analysis results reflected in class_storage_hint. Union type parameters forced to ref (gc_managed).
- Self-contained C++ output: auto-generated declaration headers for extern modules.

## 2026-03-20 | v0.15.0

- PowerShell backend added. Generates native PowerShell code directly.
- Zig backend: pathlib native implementation + generic native re-export mechanism → 18/18 parity achieved.
- Go/Lua fixture parity improvements (wave 2).
- Ruby emitter: fixture parity improvements (Is/IsNot, lambda, str iteration, dunder methods, runtime extensions).
- C# emitter: @extern delegation code generation + build pipeline fixes.

## 2026-03-18 | v0.14.0

- Recursive union types (tagged unions) supported. spec-tagged-union.md established.
- Nominal ADT: parser → EAST3 lowering → C++ backend implemented end-to-end.
- Match/case exhaustiveness check (closed nominal ADT family).
- Non-C++ backends fail-closed on nominal ADT lane.

## 2026-03-14–17

- EAST core module decomposition (core.py 8000 lines → 20+ files).
- IR core decomposition: builder, expr, stmt, call metadata, type parser etc. into individual modules.
- Backend registry selfhost parity strengthening. Local CI reentry guard.

## 2026-03-11–13 | v0.13.0

- Built an NES (Famicom) emulator in Python + SDL3. Improving Pytra to enable C++ transpilation.
- Linker spec established (spec-linker.md). Compile / link pipeline plan.
- Common smoke test infrastructure for all backends. `test_py2x_smoke_common.py` as source of truth.
- Non-C++ backend health gate aggregated by family.

## 2026-03-10 | v0.12.0

- Major runtime reorganization. C++ generated runtime header generation pipeline established.
- `src/runtime/cpp/{generated,native}` responsibility separation established.
- Runtime .east files as source of truth, with automatic C++ header generation.

## 2026-03-09 | v0.11.0

- Object boundary redesign. Selfhost stage2 parity (pass=18 fail=0) achieved.
- Tutorial setup (tutorial/README.md, how-to-use.md).

## 2026-03-08 | v0.10.0

- `@template` now usable. v1 for linked runtime helpers.
- Runtime for each language under development. Debian 12 parity bootstrap.
- Completion criteria defined for all-target sample parity.

## 2026-03-07 | v0.9.0

- Major refactoring completed. All languages usable again.
- `@extern` and `@abi` now usable, enabling transpiled code to be called from other languages.
- Selfhost stage1 build + direct .py route green.

## 2026-03-06 | v0.8.0

- ABI boundary redefined, major refactoring in progress.
- spec-abi.md established (@extern / @abi fixed ABI types).
- Non-C++ transpilers temporarily broken.

## 2026-03-04 | v0.7.0

- PHP added as a transpilation target. Nim formal support in progress.

## 2026-03-02 | v0.6.0

- Scala added as a transpilation target.

## 2026-03-01 | v0.5.0

- Lua added as a transpilation target.

## 2026-02-28 | v0.4.0

- Ruby added as a transpilation target.

## 2026-02-27 | v0.3.0

- EAST (intermediate representation) reorganized into staged processing (EAST1 → EAST2 → EAST3).
- Major decomposition / reduction of C++ CodeEmitter.

## 2026-02-25 | v0.2.0

- All languages (C++, Rust, C#, JS, TS, Go, Java, Kotlin, Swift) now output code closely resembling the original source.

## 2026-02-23 | v0.1.0

- Pytra initial release. Generates highly readable C++ code that closely mirrors the original Python source style.
