# P5-PARITY-EMIT-UNIFY: Unify emit logic in runtime_parity_check_fast.py

Last updated: 2026-04-03

## Background

The `_transpile_in_memory` function in `tools/check/runtime_parity_check_fast.py` contains an if/elif chain for 18 languages. It directly imports `emit_<lang>_module` for each language, with hand-written module_kind branching, runtime copying, and emit context injection per language. Every time a new language is added, the parity check must be modified.

On the other hand, each language's `cli.py` has already been migrated to the common runner (`toolchain2.emit.common.cli_runner`), unified with emit function + post_emit.

## Approach

Since parity check is under `tools/` and is not a selfhost target, dynamic import via `importlib` can be used. Simplify the emit logic as follows:

```python
import importlib

def _emit_modules(linked_modules, target, output_dir):
    # Get emit function via dynamic import
    lang = "ts" if target == "js" else target
    mod = importlib.import_module(f"toolchain2.emit.{lang}.emitter")
    emit_fn = getattr(mod, f"emit_{lang}_module")

    for m in linked_modules:
        code = emit_fn(m.east_doc)
        if code.strip() == "":
            continue
        out_name = m.module_id.replace(".", "_") + _ext_for_target(target)
        output_dir.joinpath(out_name).write_text(code, encoding="utf-8")

    # Also get post_emit (runtime copy) dynamically
    try:
        cli_mod = importlib.import_module(f"toolchain2.emit.{lang}.cli")
        post_emit = getattr(cli_mod, "_copy_{lang}_runtime", None)
        if post_emit:
            post_emit(output_dir)
    except (ImportError, AttributeError):
        pass
```

### Special handling for C++

C++ uses `direct_emit_fn(east_doc, output_dir) → int` rather than `emit_fn(east_doc) → str`. When C++ is detected in the parity check, call `_emit_cpp_direct` (already defined in cli.py). Only one `if` branch for C++ remains, but the 18-language if/elif chain disappears.

### Items to be removed

- The 18-language if/elif chain inside `_transpile_in_memory`
- Static imports at the top of the file: `from toolchain2.emit.<lang>.emitter import emit_<lang>_module` for each language
- Duplicate `_copy_<lang>_runtime` function implementations inside the parity check
- The `_inject_basic_module_id` helper (superseded by the `_cli_*` metadata from the common runner)

### Handling inconsistent emit function names

Some languages have inconsistent emit function names (ruby: `transpile_to_ruby`, powershell: `emit_ps`). When dynamic import looks for `emit_{lang}_module` and doesn't find it, try fallback names. Alternatively, add an `emit_{lang}_module` alias in each language's emitter.py to unify them (this is the preferred approach).

## Target

- `tools/check/runtime_parity_check_fast.py` — unify the emit loop
- Each language's `emitter.py` — unify emit function names (where needed)

## Out of scope

- Changes to `toolchain2/emit/common/cli_runner.py` (already complete)
- Changes to `pytra-cli2.py` (no changes needed; called via subprocess)
- Changes to emitter logic itself

## Acceptance Criteria

- [ ] The if/elif chain in `_transpile_in_memory` has been replaced with dynamic import-based logic
- [ ] Parity check does not need to be modified when a new language is added
- [ ] No regression in C++ parity (a single branch for C++ using direct_emit_fn is acceptable)
- [ ] Parity check works for all existing languages

## Subtasks

1. [ ] [ID: P5-PARITY-EMIT-S1] Unify emit function names to `emit_<lang>_module` in each language's emitter.py (ruby: add alias for `transpile_to_ruby`, powershell: add alias for `emit_ps`)
2. [ ] [ID: P5-PARITY-EMIT-S2] Replace the emit loop in `_transpile_in_memory` with dynamic import + a common loop
3. [ ] [ID: P5-PARITY-EMIT-S3] Remove duplicate `_copy_<lang>_runtime` implementations from the parity check and delegate to post_emit in cli.py
4. [ ] [ID: P5-PARITY-EMIT-S4] Confirm no regression in parity check for all languages (representative fixture cases)

## Decision Log

- 2026-04-03: Migration of each language's cli.py to the common runner is complete. Filed a plan to apply the same pattern to unify the emit logic in the parity check.
