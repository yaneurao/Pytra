<a href="../../ja/tutorial/transpiler-cli.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Transpiler CLI Usage

This page covers how to use `pytra-cli.py` / `toolchain/emit/cpp.py` directly, rather than through the unified CLI `./pytra`.
For normal usage, see [how-to-use.md](./how-to-use.md) first.

## Command Prerequisites by OS

Command examples on this page are written for POSIX shells (bash/zsh).
On Windows, rewrite commands as follows.

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

## Transpiler Usage by Language

Expand only the section for the language you need.

<details>
<summary>C++</summary>

### Shortest Path (Unified CLI)

```bash
# Transpile + build + run in one command
./pytra INPUT.py --target cpp --build --run --output-dir out --exe app.out
```

### compile → link → emit Pipeline (pytra-cli.py + toolchain/emit/cpp.py directly)

C++ transpilation internally passes through three stages: compile → link → emit.

```bash
# 1) Single-file output (simplest)
PYTHONPATH=src python src/pytra-cli.py INPUT.py --target cpp -o out/main.cpp

# 2) Three-stage pipeline (via intermediate .east + linked EAST)
# Stage 1: compile + link → linked EAST
PYTHONPATH=src python src/pytra-cli.py INPUT.py --target cpp --link-only --output-dir out/linked/

# Stage 2: linked EAST → C++ multi-file (toolchain/emit/cpp.py uses C++ emitter only)
PYTHONPATH=src python src/toolchain/emit/cpp.py out/linked/link-output.json --output-dir out/cpp/

# 3) g++ build (for single-file output)
g++ -std=c++20 -O2 -I src -I src/runtime/cpp out/main.cpp \
  src/runtime/cpp/core/gc.cpp src/runtime/cpp/core/io.cpp \
  src/runtime/cpp/std/math.cpp src/runtime/cpp/std/time.cpp \
  src/runtime/cpp/std/sys.cpp \
  -o out/app.out
./out/app.out
```

Notes:
- `toolchain/emit/cpp.py` is a standalone entry point that imports only the C++ backend. It does not include non-C++ backend dependencies.
- `--link-only` outputs `link-output.json` (manifest) and linked EAST3 JSON.

### Runtime Layout

`src/runtime/cpp/` follows a namespace-based directory structure:
- `core/` — type definitions (`py_types.h`), GC (`gc.h`), IO (`io.h`), process management
- `built_in/` — built-in operations (`base_ops.h`, `contains.h`, `list_ops.h`, etc.)
- `std/` — standard library support (`math.cpp`, `time.cpp`, `sys.cpp`, etc.)

The Python source of truth for runtime modules lives under `src/pytra/`, and `.east` (EAST3 JSON) files are placed in `src/runtime/east/`.

Notes:
- Importable modules are limited to those under `src/pytra/` and user-authored `.py` modules.
- User module imports accept both absolute and relative `from-import` forms.
- The `pytra` namespace is reserved. A `pytra.py` file in the same directory as the input file is not allowed.
- Unresolved or circular user-module imports fail early with `[input_invalid]`.
- For C++ performance comparisons, use `-O3 -ffast-math -flto`.

### Options

- Index bounds check: `--bounds-check-mode {always,debug,off}` (default: `off`)
- Division semantics: `--floor-div-mode {native,python}` / `--mod-mode {native,python}` (default: `native`)
- Integer bit width: `--int-width {32,64}` (default: `64`)
- EAST3 optimization level: `--east3-opt-level {0,1,2}` (default: `1`)

</details>

<details>
<summary>Rust</summary>

```bash
python src/pytra-cli.py --target rs test/fixtures/collections/iterable.py -o work/transpile/rs/iterable.rs
rustc -O work/transpile/rs/iterable.rs -o work/transpile/obj/iterable_rs.out
./work/transpile/obj/iterable_rs.out
```

Notes:
- Place runtime implementations for Python modules used by input code under `src/runtime/rs/`.

</details>

<details>
<summary>Ruby</summary>

```bash
python src/pytra-cli.py --target ruby test/fixtures/collections/iterable.py -o work/transpile/ruby/iterable.rb
ruby work/transpile/ruby/iterable.rb
```

Notes:
- `pytra-cli.py --target ruby` generates Ruby code directly from EAST3 via the native emitter (`src/toolchain/emit/ruby/emitter/ruby_native_emitter.py`).
- Image output APIs (`png.write_rgb_png` / `save_gif`) are currently handled by no-op runtime hooks; use this primarily for syntax/execution-path regression at this stage.
- Check transpile regressions with `python3 tools/check_py2rb_transpile.py`.
- Run parity with `python3 tools/runtime_parity_check.py --case-root sample --targets ruby` (environments without Ruby toolchain are recorded as `toolchain_missing`). Unstable timing lines such as `elapsed_sec` are excluded from comparison by default.

</details>

<details>
<summary>Lua</summary>

```bash
python src/pytra-cli.py --target lua test/fixtures/collections/iterable.py -o work/transpile/lua/iterable.lua
lua work/transpile/lua/iterable.lua
```

Notes:
- `pytra-cli.py --target lua` generates Lua code directly from EAST3 via the native emitter (`src/toolchain/emit/lua/emitter/lua_native_emitter.py`).
- Image APIs (`png.write_rgb_png` / `save_gif`) are currently handled by stub/no-op runtime.
- Check transpile regressions with `python3 tools/check_py2lua_transpile.py` (currently monitors with expected failures excluded).
- Run parity with `python3 tools/runtime_parity_check.py --case-root sample --targets lua 17_monte_carlo_pi` (environments without Lua toolchain are recorded as `toolchain_missing`). Unstable lines are excluded by default.
- `sample/lua` currently has `02_raytrace_spheres` / `03_julia_set` / `04_orbit_trap_julia` / `17_monte_carlo_pi` regenerated.

</details>

<details>
<summary>PHP</summary>

```bash
python src/pytra-cli.py --target php test/fixtures/collections/iterable.py -o work/transpile/php/iterable.php
php work/transpile/php/iterable.php
```

Notes:
- `pytra-cli.py --target php` generates PHP code directly from EAST3 via the native emitter (`src/toolchain/emit/php/emitter/php_native_emitter.py`).
- Canonical PHP runtime helpers live under `src/runtime/php/{generated,native}/`, and transpilation stages only the required helpers into `work/transpile/php/`.
- Check transpile regressions with `python3 tools/check_py2php_transpile.py`.
- Run parity with `python3 tools/runtime_parity_check.py --case-root sample --targets php` (environments without PHP toolchain are recorded as `toolchain_missing`).

</details>

<details>
<summary>C#</summary>

```bash
python src/pytra-cli.py --target cs test/fixtures/collections/iterable.py -o work/transpile/cs/iterable.cs
python3 tools/check_py2cs_transpile.py
```

Notes:
- `pytra-cli.py --target cs` is an EAST-based transpiler (`.py/.json -> EAST -> C#`).
- For C# output quality improvements, see `docs/en/todo/index.md`.

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/pytra-cli.py --target js test/fixtures/collections/iterable.py -o work/transpile/js/iterable.js
node work/transpile/js/iterable.js
```

Notes:
- `browser` / `browser.widgets.dialog` are treated as external references; `pytra-cli.py --target js` does not generate import bodies for them.

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/pytra-cli.py --target ts test/fixtures/collections/iterable.py -o work/transpile/ts/iterable.ts
npx tsx work/transpile/ts/iterable.ts
```

Notes:
- `pytra-cli.py --target ts` is an EAST-based preview output (migration to a dedicated TSEmitter is in progress).
- Current output is TypeScript based on JavaScript-compatible code.

</details>

<details>
<summary>Go</summary>

```bash
python src/pytra-cli.py --target go test/fixtures/collections/iterable.py -o work/transpile/go/iterable.go
go run work/transpile/go/iterable.go
```

Notes:
- `pytra-cli.py --target go` generates Go code directly from EAST3 via the native emitter (`src/toolchain/emit/go/emitter/go_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Java</summary>

```bash
python src/pytra-cli.py --target java test/fixtures/collections/iterable.py -o work/transpile/java/iterable.java
javac work/transpile/java/iterable.java
java -cp work/transpile/java iterable
```

Notes:
- `pytra-cli.py --target java` generates Java code directly from EAST3 via the native emitter (`src/toolchain/emit/java/emitter/java_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Swift</summary>

```bash
python src/pytra-cli.py --target swift test/fixtures/collections/iterable.py -o work/transpile/swift/iterable.swift
swiftc work/transpile/swift/iterable.swift -o work/transpile/obj/iterable_swift.out
./work/transpile/obj/iterable_swift.out
```

Notes:
- `pytra-cli.py --target swift` generates Swift code directly from EAST3 via the native emitter (`src/toolchain/emit/swift/emitter/swift_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/pytra-cli.py --target kotlin test/fixtures/collections/iterable.py -o work/transpile/kotlin/iterable.kt
kotlinc work/transpile/kotlin/iterable.kt -include-runtime -d work/transpile/obj/iterable_kotlin.jar
java -cp work/transpile/obj/iterable_kotlin.jar pytra_iterable
```

Notes:
- `pytra-cli.py --target kotlin` generates Kotlin code directly from EAST3 via the native emitter (`src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py`).
- Native generation is the default (no sidecar `.js` is emitted).
- Sidecar compatibility mode has been removed; only the native path is available.

</details>

<details>
<summary>Scala3</summary>

```bash
python src/pytra-cli.py --target scala test/fixtures/collections/iterable.py -o work/transpile/scala/iterable.scala
scala run work/transpile/scala/iterable.scala
```

Notes:
- `pytra-cli.py --target scala` generates Scala3 code directly from EAST3 via the native emitter (`src/toolchain/emit/scala/emitter/scala_native_emitter.py`).
- Check transpile regressions with `python3 tools/check_py2scala_transpile.py` (validates both positive success and expected-negative error categories simultaneously).
- Run full parity (sample + positive fixture manifest) with `python3 tools/check_scala_parity.py`.
- To run sample-only parity first, use `python3 tools/check_scala_parity.py --skip-fixture`.
- `runtime_parity_check` excludes unstable timing lines such as `elapsed_sec` from comparison by default.

</details>

<details>
<summary>EAST (Python → EAST → linked EAST → C++)</summary>

This is the procedure for using the compile → link → emit pipeline via `.east` and linked EAST.

```bash
# 1) Compile Python to .east (EAST3 JSON)
PYTHONPATH=src python src/pytra-cli.py compile sample/py/01_mandelbrot.py -o out/east/01_mandelbrot.east

# 2) Link .east to linked EAST (includes type_id resolution and optimization)
PYTHONPATH=src python src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp --link-only --output-dir out/linked/

# 3) Generate C++ from linked EAST
PYTHONPATH=src python src/toolchain/emit/cpp.py out/linked/link-output.json --output-dir out/cpp/
```

Notes:
- `pytra compile` generates `.py` → `.east` (EAST3 JSON).
- `--link-only` runs compile + link + optimize and outputs linked EAST.
- `toolchain/emit/cpp.py` is the standalone entry point for linked EAST → C++ multi-file output.
- Single-file transpilation is also possible with `pytra-cli.py INPUT.py --target cpp -o OUT.cpp` (it internally runs compile → link → emit).

</details>
