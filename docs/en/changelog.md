<a href="../ja/changelog.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Changelog

## 2026-04-10

- **P0-ZIG-CREXC-S4 complete**: Zig / Rust exception / try / with / raise handling fully shared via CommonRenderer hooks. Most language-specific duplication removed from emitters.
- **Zig toolchain_ dependency removed**: `toolchain_.frontends.runtime_symbol_index` dependency eliminated. All toolchain_ dependencies now gone (Dart / Swift / Julia / Zig).
- **Zig new fixture parity verified**: with_statement / with_context_manager and other new fixtures pass on Zig.
- **Nim parity complete**: P1-NIM-EMITTER-S5/S6 done. Compile/run parity established; fixed index errors in new fixtures.
- **Go type-id helper dependency removed**: P0-GO-TYPEID-CLN-S1~S3. Legacy type-id helper gone from Go emitter.
- **Lua emitter guide violations fixed**: P0-LUA-EMITGUIDE-S1~S3. Hardcode removal, mapping-driven lowering.
- **Lua full fixture parity complete**: P1-LUA-EMITTER-S5 done.
- **P3-COPY-ELISION-S4 Lua implementation complete**: `bytes(bytearray)` copy elision in Lua runtime. Readonly proof extended across modules. png/gif copy elision path finished.

## 2026-04-09

- **P0-ZIG-CREXC-S4 continued**: Shared Zig / Rust handler binding, bound exception value builder, slot accessor, with fallback protocol calls via hooks. Rust with helpers (entry/exit target, exit action, bind cloning, close fallback, protocol call builder, hoist collection, enter/exit metadata helpers) migrated to CommonRenderer.
- **Rust panic hooks**: `panic_any`, panic capture wrapper, panic raise rendering routed through hooks.
- **Zig block expression helper sharing**: Compare block, comprehension block, guarded inline exception block, simple block expr helpers consolidated in CommonRenderer.

## 2026-04-08

- **All languages lint clear (0 violations)**: Down from 697 on Apr 4. 18 languages at 10/10 PASS.
- **C# / Go / Nim parity + stdlib parity restoration**: Migration to metadata-driven lowering, runtime metadata alignment.
- **Import binding unified**: std / helper symbol imports resolved via mapping.json.
- **Fixture gaps closed**: PS1 / Go / Nim fixture parity gaps filled.
- **Zig fixture parity restored**: Aligned with semantics.
- **P0-ZIG-CREXC S1-S3 started**: Plan to push Zig / Rust exception handling (raise / try / with) into CommonRenderer. Rs/zig user-context with, raise/try shape classification, try handling shared.
- **P0-ZIG-CREXC-S4 started**: Rs/zig exception style declared in emit profiles. Handler type/body/name access, handler dispatch loop, try match wrapper, string/user handler chain routed through hooks.
- **Nim emitter string-split workaround removed**: `"po" + "p"`, `"o" + "s"` etc. lint-avoidance tricks eliminated. Migrated to mapping-driven method lowering.
- **PowerShell emitter guide alignment**: Aligned with with-metadata and runtime mapping.
- **Rust emitter literal coupling removed**: String hardcode removed from emitter.
- **Lint: non-emitter false positive exclusion**: Lint now excludes false positives from non-emitter files.

## 2026-04-07

- **Lint down to 149 / 14 languages at 10/10 PASS**: C++, JS, TS, Dart, Swift, Julia, Zig, Java, Scala, Kotlin, Ruby, Lua, PHP, Nim (Nim 9/10). Down from 697 on Apr 4.
- **PyFile abolished**: Replaced fake `PyFile` type with Python's `io` module hierarchy: `IOBase` / `TextIOWrapper` / `BufferedWriter` / `BufferedReader`. Defined in `src/pytra/built_in/io.py` as `@extern class`.
- **Emitter guide §12.7 file I/O type mapping**: Documented mode-based resolved_type, io.py hierarchy, naming conventions. Emitters must not branch on type name strings. Runtime implementations must match built_in/io.py names.
- **Lint: PyFile detection**: `class_name` category detects `"PyFile"` in emitters. `rt:type_id` detects deprecated `PyFile` key in mapping.json types.
- **Cross-language PyFile coupling removal**: Removed PyFile references from Java, Swift, Ruby, Lua, C++, TS, Julia emitters.
- **Go / Rust / C# / PHP emitter guide alignment**: Mapping-driven method lowering, stale mapping cleanup, parity restoration.
- **Ruby / Lua hardcode removal + parity restoration**: Emitter hardcode cleanup and stale mapping entries removed.
- **JVM backend continued**: Java stdlib/sample parity restored. Kotlin emitter complete (sample 18/18 PASS).
- **TODO cleanup**: Archived completed tasks for C++, Swift, Julia, TS, Dart, JVM.

## 2026-04-06

- **With statement via __enter__ / __exit__ protocol**: CommonRenderer default try/finally + hoist. C++ parity PASS. Plan in `p0-with-context-manager.md`.
- **With fixtures**: `with_statement` (file I/O) and `with_context_manager` (user-defined __enter__/__exit__ call order + exception safety).
- **Parity check: keep work dir on FAIL**: Failed cases now print `[INFO] work dir kept for inspection: <path>` and preserve generated files.
- **Progress summary regeneration fix**: Changed marker from `backend-progress-fixture.md` mtime to dedicated `.parity-results/.progress_generated`.
- **pathlib_extended joinpath**: Added Path.joinpath() tests. Resolved Julia mapping-to-east coverage warning.
- **.east* removed from git**: Untracked 12 files in test/include/east1/ and 1 in src/runtime/east/. Added to .gitignore.
- **TS/JS shim cleanup complete**: Removed Python builtin shims (`int=Number` etc.) from py_runtime.ts/js. Emitter uses mapping.json.
- **Dart emitter guide compliance**: Removed toolchain_ dependency. Module-prefix hardcode removal, metadata-based method lowering/ctor/With support.
- **JVM backend major progress**: Java/Scala/Kotlin mapping.json canonicalization, fixture parity restoration. Scala/Kotlin emitters implemented. Stdlib/sample parity restored.
- **C++ / Swift / Julia / Dart with fixture support**: Each language passes with_statement fixture.
- **P2-*-LINT policy unified**: All languages' lint tasks now focus on emitter guide compliance, not just zero violations.

## 2026-04-05

- **containers.py mut[T] annotations**: Defined container method signatures as source of truth in `src/pytra/built_in/containers.py`. Resolve derives `meta.mutates_receiver: true` from `mut[T]`.
- **C++ method name hardcode removed**: Replaced mutable method name lists in emitter.py/header_gen.py with `meta.mutates_receiver`. Lint runtime_symbol 0.
- **C++ mapping.json cleanup**: Classified and removed 14 dead entries. rt:call_coverage 0.
- **C++ new fixture parity**: bytes_copy_semantics, negative_index_comprehensive, callable_optional_none, str_find_index, eo_extern_opaque_basic, math_extended, os_glob_extended all PASS.
- **mapping.json FQCN key unification**: All languages' mapping.json calls keys unified to fully qualified names.
- **Toolchain rename complete**: toolchain → toolchain_, toolchain2 → toolchain. toolchain_ gitignored.
- **New fixtures**: str_count, sorted_basic, exception_types, float_constructor.

## 2026-04-04

- **Lint: Python method name hardcode detection**: Added 23 patterns ("append", "extend", "pop", "clear" etc.) to runtime_symbol category.
- **Parity check: all-skip now FAIL**: Cases where all targets skip (missing toolchain) now report FAIL, not false PASS. Fixes Kotlin/Scala/PowerShell.
- **pytra-cli.py default output → work/tmp/**: No more stray .east files in source directories when -o is omitted.
- **Removed auto-lint from parity check**: Lint runs manually or via run_local_ci only.
- **Lint always 10 categories**: --include-runtime default ON, replaced with --skip-runtime. Cache mechanism removed.
- **callable_optional_none fixture**: Tests callable|None is-None guard + invoke. C++/Rust optional callable unwrap fixed.
- **Emitter guide §12.6 callable mapping**: All languages' callable type mapping and callable|None representation documented.
- **Emitter guide §14.1 lint docs**: All 10 categories explained, execution instructions added.
- **mapping.json FQCN key plan**: Bare symbols ("sin") risk collision with user functions. Plan to use "pytra.std.math.sin" (P0-MAPPING-FQCN-KEY).
- **Stray east file cleanup**: Removed from out/, src/include/, test/fixture/source/, test/stdlib/source/.
- **Nim PyObj boxing rejected**: Must use object variants per spec-adt.md §3.1.
- **Zig old toolchain edit reverted**: src/toolchain/emit/zig/ is read-only.
- **Zig fixture/stdlib**: fixture 146/146 PASS, stdlib in progress.
- **Julia fixture**: 116→145 (+29). PowerShell stdlib: 0→6 (+6).

## 2026-04-03

- **Unified emitter call structure**: New common runner `cli_runner.py`. 17 languages migrated (Rust only exception). `pytra-cli.py` calls cli.py via subprocess, no direct emitter imports.
- **Parity check emit unification**: Replaced 18-language if/elif chain with importlib dynamic import + common loop.
- **`resolved_type: "object"` banned globally**: EAST3 validator fail-fast. Trait `cls: object` → `@template T`, dict.get() type inference bug fixed.
- **IsInstance PYTRA_TID_* removed**: Migrated to `expected_type_name`. C++ reverse lookup table deleted.
- **`--east3-opt-level` → `--opt-level` rename**: Integrated negative_index/bounds_check preset.
- **@extern class opaque type**: spec finalized, class_storage_hint:"opaque" + meta.opaque_v1. New `eo_` prefix for emit-only fixtures.
- **builtin_name removed**: Deleted from EAST3 compile/resolve. mapping.json keys unified to runtime_call.
- **runtime_call coverage lint**: New `rt: call_cov` category in emitter-hardcode-lint.md.
- **Lint always 10 categories**: `--include-runtime` default ON. Removed auto-lint from parity check.
- **All-skip now FAIL**: Parity check reports FAIL when all targets skip (missing toolchain).
- **tools/unregistered/ deleted**: 110 retired scripts removed.
- **check_todo_priority.py deleted**: Impractical priority checker removed.
- **Julia / Zig / PowerShell / Swift / Dart backend TODOs**: Toolchain2 emitter tasks created for each.
- **Kotlin / Scala merged into JVM backend TODO**: Managed in java.md.

## 2026-04-02

- **C++ monostate → optional\<variant\>**: `T1 | T2 | None` mapping changed from `std::variant<..., std::monostate>` to `std::optional<std::variant<...>>`. Aligned with Rust `Option<enum>`.
- **C++ bounds check / negative index → EAST optimizer**: Migrated to `subscript_access_v1` metadata. Sample 01 mandelbrot 12.8s → 0.82s.
- **png.py / gif.py extend optimization**: Replaced append loops with extend. Speeds up PNG/GIF for all languages.
- **bytes_copy_semantics fixture**: Verifies bytes(bytearray) makes independent copy.
- **negative_index fixtures**: comprehensive + out_of_range.
- **emitter guide §12.4-12.6**: Optional/union type mapping, callable type mapping for all languages.
- **Emitter lint improvements**: runtime cache, total_cats denominator fix.
- **Fixture rename**: any_* → union_*/optional_none.
- **Java / C# tasks archived**. Badge order unified (JVM grouped).

## 2026-04-01

- **Emitter lint runtime cache**: --include-runtime results cached and restored on normal runs.
- **Source-of-truth modification prohibition**: src/pytra/utils/*.py and src/pytra/std/*.py may not be modified by backend agents.
- **EAST3 copy elision plan**: Planned copy_elision_safe_v1 metadata for bytes(bytearray) optimization.
- **C++ prefix_match lint fix**: Removed pytra.std. fallback from runtime_paths.py.

## 2026-03-31

- **Ruby / Lua / PHP / Nim backend teams added**: TODO and plans created for each language.
- **C# emitter pre-selfhost complete**: fixture 131/131 + sample 18/18 + stdlib 16/16 PASS. Lint all categories 0. Added dotnet fallback to parity check.
- **C# / Java emitter progress**: Java S1/S2 complete.
- **spec-python-compat: bool is NOT a subtype of int**: isinstance(True, int) returns False in Pytra.
- **spec-emitter-guide §15 FAQ expanded**: unsigned right shift, package manager prohibition, type check skip prohibition, yields_dynamic cast guidance.
- **spec-emitter-guide §13 selfhost parity**: Added `run_selfhost_parity.py` as canonical tool. Defined selfhost completion criteria (emit → build → golden → fixture parity → sample parity).
- **spec-emitter-guide §1.1 new prohibition**: Banned per-arity tuple `in` specialization. Must use iterable generic contains.
- **EAST3 narrowing Cast node**: Rust team implemented Cast node insertion after isinstance narrowing.
- **EAST tuple unpack bugfix**: Fixed 3 patterns — parenthesized LHS `(x,y,z)=`, bracket LHS `[x,y,z]=`, comprehension + unpack.
- **spec-east.md §4.1 Python → EAST node conversion table**: Comprehensive table for all categories (assignment/unpack, loops, functions/closures, control flow, expressions, classes, imports, container operations).
- **C++ callable type support**: `callable[[Args],Ret]` → `std::function<R(Args...)>`.
- **C++ range in arithmetic expansion**: `x in range(start, stop, step)` expanded to arithmetic check.
- **C++ variant migration plan**: Replace `object` / box / unbox with `std::variant`. Verified basic operation, recursive types, RC sharing in `work/tmp/variant_test.cpp`. Phase 1 S1 complete.
- **C++ selfhost S0-S4 complete**: All modules emit success, golden placed. S5 (build) onwards remaining.
- **C++ lint all categories PASS**: P1-CPP-LINT-CLEANUP all 5 items resolved. Removed pytra.std. blanket skip from skip_modules.
- **C++ g_type_table removed**: Switched to deleter pointer in ControlBlock. fixture 131/131 + sample 18/18 PASS.
- **C++ integer literal redundant cast removal**: Added `literal_nowrap_ranges` table to CommonRenderer. Profile-driven bare literal / typed wrap switching.
- **Rust in operator generalized**: Replaced per-arity PyContains with slice.contains().
- **EAST3 optimizer in-literal expansion**: Small literal `in` expanded to `||` chain.
- **Rust inheritance ref consistency + super() resolution**: Base class ref promotion, super() type resolution in EAST2/EAST3.
- **Rust fixture 132/132 + sample 18/18 PASS**: New emitter implementation, mapping.json, stdlib argparse parity PASS.
- **Rust selfhost mod structure plan**: Designed migration from flat include! to Rust mod + use structure.
- **Linker receiver_storage_hint**: Peer module class info attached to Attribute/Call nodes.
- **pytra-cli.py C++/Rust emit subprocess delegation**: Selfhost no longer pulls in other language emitters.
- **Parity changelog auto-recording**: PASS count changes auto-appended to progress-preview/changelog.md. Emitter lint changes also recorded.
- **Emitter lint skip_pure_python category**: Detects pure Python modules in skip_modules. Added cli.py to exclusion list.
- **New fixtures**: tuple_unpack_variants, typed_container_access, in_membership_iterable, callable_higher_order, object_container_access.
- **spec-setup.md**: Consolidated clone setup instructions (golden + runtime east).
- **spec-adt.md**: ADT specification — union type conversion per language (17 languages), recursive type handling, RC management rules, object fallback banned.
- **Output path cleanup**: sample → sample-preview, progress → progress-preview, runtime east gitignored.
- **Auto-generation intervals**: progress 3min, emitter lint 10min, selfhost 15min, benchmark 3min.
- **TODO archive cleanup**: Merged date-split files (20260330-go.md, 20260330-p10reorg.md, 20260321b.md).
- **P7-GO-SELFHOST-RUNTIME filed**: 3 gaps identified for Go selfhost binary.
- **All-language selfhost TODO parity steps**: Added `run_selfhost_parity.py` fixture/sample parity to all language TODOs.
- **Dockerfile: add TypeScript compiler**: `npm install -g typescript`. npm dependency eliminated (tsc + node).
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

- **Pipeline redesign completed**: All 6 stages of the pipeline (`parse → resolve → compile → optimize → link → emit`) via `pytra-cli` are fully operational. toolchain2 is a completely independent implementation with no dependency on toolchain.
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
- **pytra-cli**: New CLI with -parse/-resolve/-compile/-optimize/-link/-emit/-build subcommands.
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
