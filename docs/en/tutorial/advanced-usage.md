<a href="../../ja/tutorial/advanced-usage.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Advanced Usage

This page covers advanced transpilation routes and runtime helper annotations (primarily `@abi`) that are not included in [how-to-use.md](./how-to-use.md).

## C++ Max-Opt Route

- `./pytra ... --target cpp --codegen-opt 3` uses the linked-program optimizer route rather than the C++ compat route.
- With `--build`, Pytra continues from linked-program optimization into multi-file output, Makefile generation, and build.
- Intermediate linked bundles are written under `--output-dir/.pytra_linked/`.
- `--codegen-opt 0/1/2` keeps the legacy route.
- Route changes must be guarded not only by representative CLI tests but also by sample parity.

```bash
./pytra sample/py/18_mini_language_interpreter.py \
  --target cpp \
  --codegen-opt 3 \
  --build \
  --output-dir out/sample18_maxopt \
  --opt -O3 \
  --exe sample18.out
```

Verification command:

```bash
python3 tools/runtime_parity_check.py \
  --targets cpp \
  --case-root sample \
  --all-samples \
  --cpp-codegen-opt 3 \
  --east3-opt-level 2
```

## `@abi` in Runtime Helpers

- `@abi` is an annotation for fixing the boundary ABI of runtime helpers. It is not intended as a general user-code feature.
- Canonical modes are `default` / `value` / `value_mut` on the `args` side, and `default` / `value` on the `ret` side.
- `value` on arguments means a read-only value ABI. The old `value_readonly` spelling is a migration alias and is normalized to `value` in metadata.

```python
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

## `pytra-cli.py` / `pytra-cli.py` Entry Split

- Use `src/pytra-cli.py` for normal host execution. Target backends are loaded lazily per selected language.
- Use `src/pytra-cli.py` for selfhost execution. Backends are fixed to static eager imports only.
- Existing `py2{lang}.py` wrappers are compatibility-only paths; normal execution is unified on `pytra-cli.py` / `pytra-cli.py`.

```bash
# Normal execution (host-lazy)
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add.rs

# Selfhost execution (static eager import)
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add_selfhost.rs
```

### Migration Note (`py2*.py` Compatibility Wrappers)

- Existing wrappers such as `py2rs.py`, `py2js.py`, and `py2rb.py` are deprecated compatibility paths.
- For normal usage, treat `pytra-cli.py --target <lang>` as the only primary entry point; wrappers are scheduled for phased removal.
- Layer options (`--lower-option`, `--optimizer-option`, `--emitter-option`) are standardized on the `pytra-cli.py` interface.

```bash
# Canonical entry point (recommended)
python3 src/pytra-cli.py test/fixtures/core/add.py --target rs -o out/add_py2x.rs
```

## `toolchain/emit/cpp.py` / `toolchain/emit/all.py` (EAST3 JSON → Target Backend)

- `toolchain/emit/cpp.py` is the standalone C++ backend entry point. It reads `link-output.json` and emits C++ multi-file output without importing non-C++ backends, making startup faster.
- `toolchain/emit/all.py` is the generic all-backend entry point. It runs a backend directly from `EAST3(JSON)`.
- Use them for backend-only regression checks with fixed IR inputs under `test/ir`.
- Both accept `.json` only and fail-fast on any input other than `east_stage=3`.

```bash
# 1) Build an EAST3(JSON) fixture from .py
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp \
  -o work/tmp/seed_01.cpp --dump-east3-after-opt work/tmp/01_mandelbrot.east3.json

# 2) Transpile directly from EAST3(JSON) to a target language
python3 src/toolchain/emit/all.py work/tmp/01_mandelbrot.east3.json --target rs \
  -o work/tmp/east2x_01.rs --no-runtime-hook

# 3) Backend-only smoke checks for major targets (cpp/rs/js)
python3 tools/check_east2x_smoke.py
```

Notes:
- `--lower-option key=value` / `--optimizer-option key=value` / `--emitter-option key=value` are also available in `toolchain/emit/all.py`.
- Remove `--no-runtime-hook` to also verify runtime helper copy/emission behavior.

## linked-program dump / link-only / emit

- The canonical linked-program pipeline is `pytra-cli.py --link-only` → `toolchain/emit/cpp.py` (for C++).
- `pytra-cli.py --dump-east3-dir DIR` writes raw `EAST3` documents plus `link-input.json` to `DIR` and stops.
- `pytra-cli.py --link-only --output-dir DIR` skips backend generation and writes only `link-output.json` plus linked modules to `DIR`.
- `toolchain/emit/cpp.py` reads `link-output.json` and emits C++ multi-file output.
- `toolchain/emit/all.py` remains available as the generic all-backend path.

```bash
# 1) Emit raw EAST3 documents and link-input.json from .py
python3 src/pytra-cli.py sample/py/18_mini_language_interpreter.py --target cpp \
  --dump-east3-dir out/linked_debug/raw

# 2) Compile + link + optimize to produce linked output
PYTHONPATH=src python3 src/pytra-cli.py sample/py/18_mini_language_interpreter.py \
  --target cpp --link-only --output-dir out/linked_debug/linked

# 3) Emit C++ from linked output (toolchain/emit/cpp.py — C++ backend only)
PYTHONPATH=src python3 src/toolchain/emit/cpp.py out/linked_debug/linked/link-output.json \
  --output-dir out/linked_debug/cpp

# 4) Or use toolchain/emit/all.py for the generic all-backend path
python3 src/toolchain/emit/all.py out/linked_debug/linked/link-output.json --target cpp \
  --output-dir out/linked_debug/cpp_east2x
```

Notes:
- In the linked-program route, global passes consume only the modules listed in the manifest. They do not widen the import closure by re-reading extra modules from `source_path`.
- In the linked-program route, `NonEscapeInterproceduralPass` reads only `meta.non_escape_import_closure` populated by the linker. Missing closure data becomes fail-closed unresolved state.
