# Plan: Fix C++ emitter hardcode lint violations (P1-CPP-LINT-CLEANUP)

## Background

Running `check_emitter_hardcode_lint.py --lang cpp` detects 14 violations in 4 categories.

## Violation List

### 1. class_name (3 violations)

```
emitter.py:74:  "BaseException", "Exception", "ValueError", "TypeError", "IndexError",
emitter.py:1257: if attr == "add_argument" and owner_type == "ArgumentParser":
emitter.py:2658: if bn in ("BaseException", "Exception", "RuntimeError", ...)
```

- **Line 74**: Hardcoded list of exception class names used for C++ exception type mapping
- **Line 1257**: Branch on method name + class name for `ArgumentParser.add_argument`. Should use EAST3's `semantic_tag` or `runtime_call` instead
- **Line 2658**: Check for exception base class. Should use `bases` / `class_storage_hint`, or resolve via the `types` table in `mapping.json`

**Approach**: Exception class names already exist in the `types` table in `mapping.json` — derive them from there. The `ArgumentParser` branch should use resolved information from EAST3.

### 2. runtime_symbol (1 violation)

```
emitter.py:1489: if rc in ("py_print", "py_len") and len(arg_strs) >= 1:
```

- String-matching against `runtime_call` values that have already been resolved via `mapping.json`
- Should be handled via `call_adapters` or similar

**Approach**: Add `py_print: multi_arg_print` / `py_len: ref_arg` to `call_adapters` in `mapping.json` and have the emitter branch on adapter kind.

### 3. type_id (1 violation)

```
emitter.py:2052: if tid == "" and expected_name.startswith("PYTRA_TID_"):
```

- When type_id is empty, falls back using the `PYTRA_TID_*` prefix
- The type_id should be finalized by EAST3 / the linker; a fallback in the emitter violates §1.1

**Approach**: Improve error handling in EAST3 / the linker for cases where type_id is not finalized, and remove the fallback from the emitter.

### 4. skip_pure_python (9 violations)

```
mapping.json: skip_modules contains "pytra.std." which skips pure Python module pytra.std.{argparse,collections,env,json,pathlib,random,re,template,timeit}
```

- C++ has historically skipped all of `pytra.std.` and reimplemented everything natively, a legacy debt
- Pure Python modules (argparse, json, collections, pathlib, random, re, template, timeit, env) should be transpiled

**Approach**: Remove the blanket `pytra.std.` skip from `skip_modules`, and enumerate only modules that should remain native (those that have `@extern`, such as math, os, os_path, sys, glob, time) in `skip_modules` individually. Pure Python modules become transpilation targets. Because it needs to be verified whether the C++ emitter quality is sufficient for transpilation, proceed incrementally:

1. First remove `pytra.std.env` / `pytra.std.template` / `pytra.std.timeit` (small modules) from the skip list and verify transpilation
2. If successful, expand to `pytra.std.random` / `pytra.std.collections` / `pytra.std.re`
3. Finally `pytra.std.json` / `pytra.std.argparse` / `pytra.std.pathlib` (large modules)

## Impact

- class_name / runtime_symbol / type_id fixes are confined to `emitter.py`
- skip_pure_python fix requires changes to `mapping.json` + transpilation quality verification
- Full parity check for all fixture + sample cases is required

## Completion Notes

- Added a built-in exception helper to `toolchain2.link.type_id` and eliminated the hardcoded `BaseException` / `ValueError` strings in the C++ emitter
- Changed `ArgumentParser.add_argument` special formatting to branch on `semantic_tag` and keyword calls instead of the class name
- Added `call_adapters` to `mapping.json` and migrated `py_print` / `py_len` emit branching to an adapter-based approach
- Removed the `PYTRA_TID_*` prefix fallback; only the exact constants passed by EAST3 are handled via an explicit map
- Removed the `pytra.std.` prefix from `skip_modules` and moved only the `@extern` modules that must remain native to `skip_modules_exact`
- Also fixed regressions exposed by the transpiled stdlib path (`argparse_extended`, `json_extended`) and verified representative cases for `argparse` / `json` / `pathlib` / `re` in C++ parity
