# Plan: Decouple C++-specific imports from pytra-cli2.py (P0-CLI2-CPP-DECOUPLE)

## Background

Because `pytra-cli2.py` imports `toolchain2.emit.cpp.runtime_bundle` at the top level, all language emitter modules end up in the dependency graph for Rust/Go selfhost builds, causing `cargo build` / `go build` to fail on compilation errors from modules that are not needed.

`pytra-cli2.py` is meant to be a language-agnostic pipeline entry point, so having C++-specific imports at the top level is a design violation.

## Current State

```python
# top-level imports in pytra-cli2.py
from toolchain2.emit.cpp.runtime_bundle import write_helper_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_runtime_module_artifacts
from toolchain2.emit.cpp.runtime_bundle import write_user_module_artifacts
```

These are used only inside `_emit_cpp_linked_module()` (lines 264–285), which is only called on the C++ path of the `-emit` / `-build` commands.

## Design

### Approach

Move `_emit_cpp_linked_module()` to the `toolchain2.emit.cpp` side and call it from `pytra-cli2.py` via a language-agnostic API.

### Specific Changes

1. Add `emit_cpp_linked_module(module, output_dir)` to `toolchain2.emit.cpp.cli` (or `toolchain2.emit.cpp.emit_linked`)
2. Remove `_emit_cpp_linked_module()` and the 3 `from toolchain2.emit.cpp.runtime_bundle import ...` lines from `pytra-cli2.py`
3. Call through a language dispatch table in the `-emit` / `-build` C++ path of `pytra-cli2.py`

### Language Dispatch Shape

```python
# pytra-cli2.py — language-agnostic
def _emit_linked_module(target: str, module: LinkedModule, output_dir: Path) -> int:
    if target == "cpp":
        from toolchain2.emit.cpp.emit_linked import emit_cpp_linked_module
        return emit_cpp_linked_module(module, output_dir)
    # other languages use existing paths
    ...
```

However, spec-agent.md §5 prohibits dynamic imports in selfhost target code. Therefore:

**Decision**: Delegate only the emitter call to a subprocess. parse / resolve / compile / optimize / link remain in-memory.

- `pytra-cli2.py` invokes each language's emitter as a subprocess for `-emit` / `-build`
- `pytra-cli.py` (the old CLI) already uses the same structure and passes selfhost
- The emitter is called only once at the end of the pipeline, so subprocess overhead is negligible
- In-function imports cannot be transpiled by Pytra, so subprocess is the only viable approach

## Impact

- Fewer imports in `pytra-cli2.py` (C++ dependency removed)
- Behavior of `-build` for C++ is unchanged (internal refactor only)
- C++ emitter no longer enters the dependency graph for Rust/Go selfhost
- Full parity check across all languages for fixture + sample is required

## Completion Notes

- Added `src/toolchain2/emit/cpp/cli.py` and moved manifest loading and per-linked-module C++ emit to the C++ side
- `src/pytra-cli2.py` no longer imports `toolchain2.emit.cpp.runtime_bundle`; C++ emit is now unified under a `python3 -m toolchain2.emit.cpp.cli` subprocess
- The `-build` C++ path also goes through the same subprocess emit after writing the link result
- Added and updated `tools/unittest/tooling/test_pytra_cli2.py` as a regression check; confirmed `pytra-cli2.py -build ... --target cpp` succeeds for sample/fixture representatives
- Re-ran `runtime_parity_check_fast.py --targets cpp --case-root sample --east3-opt-level 2` as a C++ codegen non-regression check and confirmed `18/18 PASS`
