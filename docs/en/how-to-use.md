<a href="../ja/how-to-use.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Usage Guide

This document is an execution runbook for actually running Pytra.  
For normative input constraints and usage rules, see [User Specification](./spec/spec-user.md).

## Command Prerequisites by OS

Command examples in this document are written for POSIX shells (`bash` / `zsh`).
For Windows, rewrite commands as follows.

- Python execution:
  - POSIX: `python ...`
  - Windows: `py ...` (or `python ...`)
- Temporary environment variable assignment:
  - POSIX: `PYTHONPATH=src python ...`
  - Windows PowerShell: `$env:PYTHONPATH='src'; py ...`
  - Windows cmd.exe: `set PYTHONPATH=src && py ...`
- Multi-line continuation:
  - POSIX: `\`
  - Windows PowerShell: `` ` ``
  - Windows cmd.exe: `^`

## Unified CLI (`./pytra`) Usage

Root `./pytra` is a unified launcher that calls `python3 src/pytra-cli.py`.

```bash
# Help
./pytra --help

# Single-file C++ output
./pytra test/fixtures/core/add.py --output /tmp/add.cpp

# Multi-file C++ output (with manifest)
./pytra test/fixtures/core/add.py --output-dir out/add_case

# Transpile + build + run
./pytra test/fixtures/core/add.py --build --output-dir out/add_case --exe add.out --run
```

Notes:
- At this point, `./pytra` supports `--target cpp` only.
- Generated-code optimization level can be set via `--codegen-opt {0,1,2,3}`.
- In `--build` mode, generated artifacts (`src/*.cpp`, `include/*.h`, `.obj/*.o`, executable) are written under `--output-dir` (default: `out/`).
- `--exe` sets executable name/output path. Relative values (for example `add.out`) are generated under `--output-dir`.
- For temporary outputs, prefer consolidating into `out/`. Example: `./pytra INPUT.py --build --output-dir /out/mycase --exe app.out`

## Constraints To Check First

- Do not directly import Python standard-library modules such as `json`, `pathlib`, `sys`, `os`, `glob`, `argparse`, `re`, `dataclasses`, or `enum`.
- Exception: `typing` imports are allowed as annotation-only no-op imports (`import typing`, `from typing import ...`) and are not kept as runtime/dependency imports.
- Exception: `dataclasses` imports are allowed as decorator-resolution no-op imports (`import dataclasses`, `from dataclasses import ...`) and are not kept as runtime/dependency imports.
- Allowed imports are:
  - Modules under `src/pytra/` (`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`)
  - User-authored `.py` modules
- User module import is valid by specification, but multi-file dependency resolution is still being implemented in phases.
- See [Module Index](./spec/spec-pylib-modules.md) for supported modules and APIs.
- See [Option Specification](./spec/spec-options.md) for option policy and candidates.
- See [Tools Guide](./spec/spec-tools.md) for helper script purposes.
- For normative constraint definitions, see [User Specification](./spec/spec-user.md).

## Runtime Measurement Protocol (sample)

- For runtime measurements from `sample/py`, measure after fresh transpile.
- Default measurement count is `warmup=1` + `repeat=2`.
- Use the **arithmetic mean (average)** of the two measured runs as the representative value (do not use median).
- Exclude compile time from runtime numbers.

## Runtime Parity Runbook (sample, all targets)

- `tools/runtime_parity_check.py` validates not only stdout but also artifact `size` and `CRC32` from each `output:` path.
- During parity runs, stale artifacts are purged per case from `sample/out`, `test/out`, `out`, and `test/transpile/<target>/<case>`.
- Unstable timing lines such as `elapsed_sec` are excluded by default (`--ignore-unstable-stdout` is compatibility-only).
- Full 14-target check:

```bash
python3 tools/runtime_parity_check.py \
  --case-root sample \
  --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua,scala,php,nim \
  --all-samples \
  --summary-json work/logs/runtime_parity_sample_all_targets.json
```

- Recommended split (faster iteration):
  - `01-03`: `01_mandelbrot 02_raytrace_spheres 03_julia_set`
  - `04-06`: `04_orbit_trap_julia 05_mandelbrot_zoom 06_julia_parameter_sweep`
  - `07-09`: `07_game_of_life_loop 08_langtons_ant 09_fire_simulation`
  - `10-12`: `10_plasma_effect 11_lissajous_particles 12_sort_visualizer`
  - `13-15`: `13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop`
  - `16-18`: `16_glass_sculpture_chaos 17_monte_carlo_pi 18_mini_language_interpreter`

## Mandatory Emitter Guardrails (Stop-Ship)

- If you modify `src/backends/*/emitter/*.py`, run the following before commit:
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- If any of them returns `FAIL`, do not commit/push (Stop-Ship).
- Runtime/stdlib call resolution must use EAST3 canonical fields only (`runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`). Do not add per-symbol branches or dispatch tables in emitters.
- `java` backend is strict: direct dispatch symbol literals are not allowlisted and must remain zero.

## `py2x.py` / `py2x-selfhost.py` Entry Split

- Use `src/py2x.py` for normal host execution. Target backends are loaded lazily per selected language.
- Use `src/py2x-selfhost.py` for selfhost execution. Backends are fixed to static eager imports only.
- Existing `py2{lang}.py` wrappers are compatibility-only paths; normal execution is unified on `py2x.py` / `py2x-selfhost.py`.

```bash
# Normal execution (host-lazy)
python3 src/py2x.py test/fixtures/core/add.py --target rs -o out/add.rs

# Selfhost execution (static eager import)
python3 src/py2x-selfhost.py test/fixtures/core/add.py --target rs -o out/add_selfhost.rs
```

### Migration Note (`py2*.py` compatibility wrappers)

- Existing wrappers such as `py2rs.py`, `py2js.py`, and `py2rb.py` are deprecated compatibility paths.
- For normal usage, treat `py2x.py --target <lang>` as the only primary entrypoint, and wrappers as phased-removal compatibility paths.
- Layer options (`--lower-option`, `--optimizer-option`, `--emitter-option`) are standardized on the `py2x.py` interface.

```bash
# Canonical entrypoint (recommended)
python3 src/py2x.py test/fixtures/core/add.py --target rs -o out/add_py2x.rs
```


## `ir2lang.py` (EAST3 JSON -> target backend)

- `ir2lang.py` runs a backend directly from `EAST3(JSON)` without passing through the frontend (`.py -> EAST3`).
- Use it for backend-only regression checks with fixed IR inputs under `sample/ir` and `test/ir`.
- It accepts `.json` only and fail-fast rejects any input other than `east_stage=3`.

```bash
# 1) Build an EAST3(JSON) fixture from .py
python3 src/py2x.py sample/py/01_mandelbrot.py --target cpp \
  -o out/seed_01.cpp --dump-east3-after-opt sample/ir/01_mandelbrot.east3.json

# 2) Transpile directly from EAST3(JSON)
python3 src/ir2lang.py sample/ir/01_mandelbrot.east3.json --target rs \
  -o out/ir2lang_01.rs --no-runtime-hook

# 3) Backend-only smoke checks for major targets (cpp/rs/js)
python3 tools/check_ir2lang_smoke.py
```

Notes:
- `ir2lang.py` supports `--lower-option key=value`, `--optimizer-option key=value`, and `--emitter-option key=value`.
- Remove `--no-runtime-hook` when you also want to verify runtime helper copy/emission behavior.

## Transpiler Usage

Use only the target language section you need.

<details>
<summary>C++</summary>

```bash
python src/py2x.py --target cpp test/fixtures/collections/iterable.py -o test/transpile/cpp/iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src -I src/runtime/cpp test/transpile/cpp/iterable.cpp \
  src/runtime/cpp/generated/utils/png.cpp src/runtime/cpp/generated/utils/gif.cpp \
  src/runtime/cpp/native/std/math.cpp src/runtime/cpp/native/std/time.cpp src/runtime/cpp/generated/std/pathlib.cpp \
  src/runtime/cpp/generated/built_in/type_id.cpp \
  src/runtime/cpp/native/core/gc.ext.cpp src/runtime/cpp/native/core/io.ext.cpp \
  -o test/transpile/obj/iterable.out
./test/transpile/obj/iterable.out
```

Notes:
- For C++ performance comparison, use `-O3 -ffast-math -flto`.
- Imports in Python input are limited to `src/pytra/` modules and user modules (example: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`, `from pytra.utils.assertions import py_assert_eq`).
- Prepare target-language runtime implementations for imported `pytra` modules under `src/runtime/cpp/`.
- GC uses `base/gc`.
- `src/runtime/cpp/` is split by responsibility into `core/`, `generated/`, `native/`, and `pytra/`.
- Generated artifacts live under `src/runtime/cpp/generated/`, C++-specific companions live under `src/runtime/cpp/native/`, and public include shims live under `src/runtime/cpp/pytra/`. The low-level core include surface remains under `src/runtime/cpp/core/`.
- `python src/py2x.py --target cpp src/pytra/<tree>/<mod>.py -o ... --header-output ...` generates `*.cpp` and `*.h` together.
- `python src/py2x.py --target cpp src/pytra/<tree>/<mod>.py --emit-runtime-cpp` writes generated artifacts to `src/runtime/cpp/generated/<tree>/...` and public shims to `src/runtime/cpp/pytra/<tree>/...` (`<tree>` = `built_in` / `std` / `utils`).
- Example: `src/pytra/built_in/type_id.py` -> `src/runtime/cpp/generated/built_in/type_id.cpp` and `src/runtime/cpp/generated/built_in/type_id.h`, with the matching public shim at `src/runtime/cpp/pytra/built_in/type_id.h`.
- Example: `src/pytra/std/math.py` is header-only, so it emits `src/runtime/cpp/generated/std/math.h`, while the native implementation stays in `src/runtime/cpp/native/std/math.cpp`.
- `src/pytra/utils/png.py` and `src/pytra/utils/gif.py` are generated with the bridge style, with type-conversion wrappers around runtime public APIs.
- `src/pytra/std/json.py` and `src/pytra/utils/assertions.py` also generate `.h/.cpp`.
- Missing native processing should be complemented in the matching `src/runtime/cpp/native/...` file (example: `src/runtime/cpp/native/std/math.cpp`).
- `png.write_rgb_png(...)` always outputs PNG (PPM output is removed).
- Use `python src/py2x.py --target cpp INPUT.py --dump-deps` to inspect import dependencies (`modules/symbols` and `graph`).
- The `pytra` namespace is reserved. `pytra.py` or `pytra/__init__.py` cannot exist in the input file directory.
- Unresolved or circular user-module imports fail early with `[input_invalid]`.
- Index bounds checks can be switched with `--bounds-check-mode {always,debug,off}` (`off` by default).
- Division semantics can be switched with `--floor-div-mode {native,python}` and `--mod-mode {native,python}` (`native` by default).
- Integer width can be selected with `--int-width {32,64,bigint}` (`bigint` not implemented).
- String index/slice semantics can be selected with `--str-index-mode {byte,codepoint,native}` and `--str-slice-mode {byte,codepoint}` (`codepoint` not implemented).
- Code-generation optimization level can be set with `-O0` to `-O3` (`-O3` default):
  - `-O0`: no optimization (investigation/debug)
  - `-O1`: light optimization
  - `-O2`: medium optimization
  - `-O3`: aggressive optimization (default)
- Option bundles can be applied with `--preset {native,balanced,python}`. Explicit per-option flags override preset values.
- Use `--dump-options` to inspect final resolved option values.
- Use `--top-namespace NS` to place generated code under a top namespace (no top namespace when omitted).
- Output mode can be selected with `--multi-file` (default) or `--single-file`.
- `--multi-file` generates `out/include`, `out/src`, and `manifest.json`.
- Use `--output-dir DIR` to control output location in multi-file mode.
- Build multi-file output with `python3 tools/build_multi_cpp.py out/manifest.json -o out/app.out`.
- In `--multi-file`, user-module import calls are converted into C++ namespace references so they are linkable.
- Verify multi-file execution consistency with `python3 tools/verify_multi_file_outputs.py --samples 01_mandelbrot`.
  - For image-output samples, binary identity of files listed in `output:` is also verified.

Examples:
- Performance priority (default):
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset native`
- Balanced compatibility:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset balanced`
- Compatibility priority (note: `int-width=bigint` is not implemented):
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset python --int-width 64`
- Inspect final resolved options:
  - `python src/py2x.py --target cpp INPUT.py --preset balanced --mod-mode native --dump-options`
- For selfhost investigation (no optimization):
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp -O0`
- Add top namespace:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --top-namespace myproj`

### Image Runtime Parity Check (Python source of truth vs C++)

Run the following to check whether outputs from `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` match outputs through `src/runtime/cpp/generated/utils/png.cpp` / `src/runtime/cpp/generated/utils/gif.cpp` (bridge).

```bash
python3 tools/verify_image_runtime_parity.py
```

</details>

<details>
<summary>Rust</summary>

```bash
python src/py2x.py --target rs test/fixtures/collections/iterable.py -o test/transpile/rs/iterable.rs
rustc -O test/transpile/rs/iterable.rs -o test/transpile/obj/iterable_rs.out
./test/transpile/obj/iterable_rs.out
```

Notes:
- Prepare corresponding implementations under `src/rs_module/` for Python modules used by input code.

</details>

<details>
<summary>Ruby</summary>

```bash
python src/py2x.py --target ruby test/fixtures/collections/iterable.py -o test/transpile/ruby/iterable.rb
ruby test/transpile/ruby/iterable.rb
```

Notes:
- `py2x.py --target ruby` generates Ruby source directly from EAST3 via the native emitter (`src/backends/ruby/emitter/ruby_native_emitter.py`).
- Image APIs (`png.write_rgb_png` / `save_gif`) are currently handled by no-op runtime hooks; use the backend primarily for syntax/execution-path regression checks at this stage.
- Check transpile regressions with `python3 tools/check_py2rb_transpile.py`.
- Run parity entry flow with `python3 tools/runtime_parity_check.py --case-root sample --targets ruby` (environments without Ruby toolchain are recorded as `toolchain_missing`). Unstable timing lines such as `elapsed_sec` are excluded from compare by default.

</details>

<details>
<summary>PHP</summary>

```bash
python src/py2x.py --target php test/fixtures/collections/iterable.py -o test/transpile/php/iterable.php
php test/transpile/php/iterable.php
```

Notes:
- `py2x.py --target php` generates PHP source directly from EAST3 via the native emitter (`src/backends/php/emitter/php_native_emitter.py`).
- Runtime helpers are managed under `src/runtime/php/pytra/` and copied into `test/transpile/php/pytra/**` when transpiling.
- Check transpile regressions with `python3 tools/check_py2php_transpile.py`.
- Run parity entry flow with `python3 tools/runtime_parity_check.py --case-root sample --targets php` (environments without PHP toolchain are recorded as `toolchain_missing`).

</details>

<details>
<summary>C#</summary>

```bash
python src/py2x.py --target cs test/fixtures/collections/iterable.py -o test/transpile/cs/iterable.cs
mcs -out:test/transpile/obj/iterable.exe \
  test/transpile/cs/iterable.cs \
  src/runtime/cs/pytra/built_in/py_runtime.cs src/runtime/cs/pytra/built_in/time.cs \
  src/runtime/cs/pytra/utils/png.cs src/runtime/cs/pytra/utils/gif.cs src/runtime/cs/pytra/std/pathlib.cs
mono test/transpile/obj/iterable.exe
```

Notes:
- Compile C# runtime implementation files from `src/runtime/cs/pytra` together with generated code.

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/py2x.py --target js test/fixtures/collections/iterable.py -o test/transpile/js/iterable.js
node test/transpile/js/iterable.js
```

Notes:
- If input uses `import`, corresponding runtime implementations under `src/runtime/js/pytra/` are required.

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/py2x.py --target ts test/fixtures/collections/iterable.py -o test/transpile/ts/iterable.ts
npx tsx test/transpile/ts/iterable.ts
```

Notes:
- If input uses `import`, corresponding runtime implementations under `src/runtime/ts/pytra/` are required.

</details>

<details>
<summary>Go</summary>

```bash
python src/py2x.py --target go test/fixtures/collections/iterable.py -o test/transpile/go/iterable.go
go run test/transpile/go/iterable.go
```

Notes:
- `py2x.py --target go` generates Go source directly from EAST3 via the native emitter (`src/backends/go/emitter/go_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Java</summary>

```bash
python src/py2x.py --target java test/fixtures/collections/iterable.py -o test/transpile/java/iterable.java
javac test/transpile/java/iterable.java
java -cp test/transpile/java iterable
```

Notes:
- `py2x.py --target java` generates Java source directly from EAST3 via the native emitter (`src/backends/java/emitter/java_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Swift</summary>

```bash
python src/py2x.py --target swift test/fixtures/collections/iterable.py -o test/transpile/swift/iterable.swift
swiftc test/transpile/swift/iterable.swift -o test/transpile/obj/iterable_swift.out
./test/transpile/obj/iterable_swift.out
```

Notes:
- `py2x.py --target swift` generates Swift source directly from EAST3 via the native emitter (`src/backends/swift/emitter/swift_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/py2x.py --target kotlin test/fixtures/collections/iterable.py -o test/transpile/kotlin/iterable.kt
kotlinc test/transpile/kotlin/iterable.kt -include-runtime -d test/transpile/obj/iterable_kotlin.jar
java -cp test/transpile/obj/iterable_kotlin.jar pytra_iterable
```

Notes:
- `py2x.py --target kotlin` generates Kotlin source directly from EAST3 via the native emitter (`src/backends/kotlin/emitter/kotlin_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Scala3</summary>

```bash
python src/py2x.py --target scala test/fixtures/collections/iterable.py -o test/transpile/scala/iterable.scala
scala run test/transpile/scala/iterable.scala
```

Notes:
- `py2x.py --target scala` generates Scala3 code directly from EAST3 via the native emitter (`src/backends/scala/emitter/scala_native_emitter.py`).
- Check transpile regressions with `python3 tools/check_py2scala_transpile.py` (it validates both positive success and expected-negative error categories).
- Run full parity (sample + positive fixture manifest) with `python3 tools/check_scala_parity.py`.
- To run sample-only parity first, use `python3 tools/check_scala_parity.py --skip-fixture`.
- `runtime_parity_check` excludes unstable timing lines such as `elapsed_sec` from comparison by default.

</details>

<details>
<summary>EAST (Python -> EAST -> C++)</summary>

```bash
# 1) Convert Python to EAST (JSON)
python src/pytra/compiler/east.py sample/py/01_mandelbrot.py -o test/transpile/east/01_mandelbrot.json --pretty

# 2) Convert EAST(JSON) to C++ (.py input can also be given directly)
python src/py2x.py --target cpp test/transpile/east/01_mandelbrot.json -o test/transpile/cpp/01_mandelbrot.cpp

# 3) Compile and run
g++ -std=c++20 -O2 -I src -I src/runtime/cpp test/transpile/cpp/01_mandelbrot.cpp \
  src/runtime/cpp/generated/utils/png.cpp src/runtime/cpp/generated/utils/gif.cpp \
  src/runtime/cpp/generated/built_in/type_id.cpp \
  src/runtime/cpp/native/core/gc.ext.cpp src/runtime/cpp/native/core/io.ext.cpp \
  -o test/transpile/obj/01_mandelbrot
./test/transpile/obj/01_mandelbrot
```

Notes:
- EAST converter: `src/pytra/compiler/east.py`
- EAST-based C++ generator: `src/py2x.py --target cpp`

</details>

## Selfhost Verification Procedure (C++ backend -> `py2cpp.cpp`)

Prerequisites:
- Run from project root.
- `g++` must be available.
- Treat `selfhost/` as a verification work directory (outside Git management).

```bash
# 0) Generate and build selfhost C++ (link runtime .cpp files too)
python3 tools/build_selfhost.py > selfhost/build.all.log 2>&1

# 1) Categorize build errors
rg "error:" selfhost/build.all.log
```

Comparison steps when compilation succeeds:

```bash
# 2) Convert sample/py/01 with selfhost executable
mkdir -p test/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp

# 3) Convert the same input with Python C++ backend
python src/py2x.py --target cpp sample/py/01_mandelbrot.py -o test/transpile/cpp/01_mandelbrot.cpp

# 4) Check generated diff (source diff is allowed; this is for inspection)
diff -u test/transpile/cpp/01_mandelbrot.cpp test/transpile/cpp2/01_mandelbrot.cpp || true

# 5) Batch-check output diff on representative cases
python3 tools/check_selfhost_cpp_diff.py --show-diff
```

Notes:
- Current `selfhost/py2cpp.py` has `load_east()` stubbed, so direct `INPUT.py` conversion is not yet supported.
- Steps from 2) onward are intended to be enabled after restoring selfhost input parser support.

Failure investigation tips:
- First classify `error:` lines in `build.all.log` into type-related (`std::any` / `optional`) vs syntax-related (missing lowering).
- At failing lines in `selfhost/py2cpp.cpp`, verify that the original `src/backends/cpp/cli.py` has not introduced extra `Any` mixing.
- `selfhost/py2cpp.py` may be stale; run `python3 tools/prepare_selfhost_source.py` before each attempt.

## Conversion Check During CodeEmitter Work

When refactoring `CodeEmitter` incrementally, run this check at each step.

```bash
python3 tools/check_py2cpp_transpile.py
```

Notes:
- By default, known negative fixtures (`test/fixtures/signature/ng_*.py` and `test/fixtures/typing/any_class_alias.py`) are excluded.
- Add `--include-expected-failures` to include negative fixtures as well.

## Common Constraints and Notes

Pytra targets a subset of Python. Even if input runs in CPython, transpilation fails when unsupported syntax is used.

For detailed support granularity in `py2cpp` (`enumerate(start)`, `lambda`, comprehensions, etc.), see `docs/en/language/cpp/spec-support.md` (with test evidence).

### 0. Error Categories

Failure messages from `src/py2x.py --target cpp` are categorized as follows.

- `[user_syntax_error]`: syntax error in user code
- `[not_implemented]`: syntax not implemented yet (future candidate)
- `[unsupported_by_design]`: syntax intentionally unsupported by language policy
- `[internal_error]`: internal transpiler error

### 1. Type Annotations and Type Inference

- Annotated code is recommended by default.
- However, annotations can be omitted for assignments whose type is uniquely determined.

```python
# Inference from literals
x = 1         # int
y = 1.5       # float
s = "hello"   # str

# Inference from known type
a: int = 10
b = a         # int
```

- Add explicit annotations where type can become ambiguous.

```python
# Cases where inference tends to be unstable
values = []              # element type unknown
table = {}               # key/value type unknown
```

### 2. Type Name Handling

Expand only the language section you need.

<details>
<summary>C++</summary>

- Primitive types: `int -> long long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
- Fixed-width integers: `int8 -> int8_t`, `uint8 -> uint8_t`, `int16 -> int16_t`, `uint16 -> uint16_t`, `int32 -> int32_t`, `uint32 -> uint32_t`, `int64 -> int64_t`, `uint64 -> uint64_t`
- Annotation alias: `byte` is treated as `uint8` (1-char / 1-byte usage).
- Byte sequences: `bytes` / `bytearray` -> `vector<uint8_t>`
- Containers:
  - `list[T] -> list<T>` (`std::vector<T>` wrapper)
  - `dict[K, V] -> dict<K, V>` (`std::unordered_map<K, V>` wrapper)
  - `set[T] -> set<T>` (`std::unordered_set<T>` wrapper)
  - `tuple[...] -> tuple<...>`
- `dict` / `set` provide Python-compatible methods (`get`, `keys`, `values`, `items`, `add`, `discard`, `remove`) in `py_runtime.h`.
- `str` / `list` / `dict` / `set` / `bytes` / `bytearray` are wrappers, not inherited STL containers.

</details>

<details>
<summary>Rust</summary>

- Primitive types: `int -> i64`, `float -> f64`, `float32 -> f32`, `str -> String`, `bool -> bool`
- Fixed-width integers: `int8 -> i8`, `uint8 -> u8`, `int16 -> i16`, `uint16 -> u16`, `int32 -> i32`, `uint32 -> u32`, `int64 -> i64`, `uint64 -> u64`
- Byte sequences: `bytes` / `bytearray` -> `Vec<u8>`
- Containers: `list[T] -> Vec<T>`, `dict[K, V] -> HashMap<K, V>`, `set[T] -> HashSet<T>`, `tuple[...] -> (...)`

</details>

<details>
<summary>C#</summary>

- Primitive types: `int -> long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
- Fixed-width integers: `int8 -> sbyte`, `uint8 -> byte`, `int16 -> short`, `uint16 -> ushort`, `int32 -> int`, `uint32 -> uint`, `int64 -> long`, `uint64 -> ulong`
- Byte sequences: `bytes` / `bytearray` -> `List<byte>`
- Containers: `list[T] -> List<T>`, `dict[K, V] -> Dictionary<K, V>`, `set[T] -> HashSet<T>`, `tuple[...] -> Tuple<...>`

</details>

<details>
<summary>JavaScript / TypeScript</summary>

- Numbers are handled as `number`.
- `bytes` / `bytearray` are handled as runtime `number[]` (`pyBytearray` / `pyBytes`).
- `list` / `tuple` become arrays, `dict` becomes map-like runtime structures, and `set` becomes set-like runtime structures.

</details>

<details>
<summary>Go</summary>

- Current implementation partly uses `any`, but numeric operations still infer `int` / `float64` / `bool` / `string`.
- `bytes` / `bytearray` are handled as `[]byte` in runtime.
- Improving Go annotation reflection to reduce `any` fallback remains an unfinished task in `docs/en/todo/index.md`.

</details>

<details>
<summary>Java</summary>

- Current implementation partly uses `Object`.
- `bytes` / `bytearray` are handled as `byte[]` in runtime.
- Improving Java annotation reflection to reduce `Object` fallback remains an unfinished task in `docs/en/todo/index.md`.

</details>

<details>
<summary>Swift / Kotlin</summary>

- Current mode runs through Node backend, so type behavior effectively follows JavaScript representation.
- Therefore numbers are handled as `number`-equivalent, and `bytes` / `bytearray` as `number[]`-equivalent.

</details>

```python
# Annotation examples
buf1: bytearray = bytearray(16)
buf2: bytes = bytes(buf1)
ids: list[int] = [1, 2, 3]
name_by_id: dict[int, str] = {1: "alice"}
```

### 3. import and Runtime Modules

- Modules importable from Python input are:
  - Modules under `src/pytra/` (`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`)
  - User-authored `.py` modules
- For each `pytra` module, target-language runtime support is required.
- That runtime support should generally be generated by transpiling `src/pytra/utils/*.py` and `src/pytra/std/*.py` into each language, minimizing handwritten code.

```python
from pytra.utils import png
from pytra.std.pathlib import Path
```

When converting the code above, the target language must also provide implementations corresponding to `pytra.utils.png` and `pytra.std.pathlib` (in principle generated from `src/pytra/utils/*.py` and `src/pytra/std/*.py`).
