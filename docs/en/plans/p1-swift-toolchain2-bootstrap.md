# P1-SWIFT-EMITTER-S1/S2 Swift toolchain2 bootstrap

Last updated: 2026-04-02

## Purpose

- Create the starting point for a Swift emitter under `src/toolchain2/emit/swift/`
- Add `src/runtime/swift/mapping.json` and the Swift pipeline in the parity harness
- Advance the Swift backend from "disconnected" to a state where fixtures can be run incrementally

## What was added in this pass

- Added `src/toolchain2/emit/swift/` and defined `emit_swift_module()` callable from toolchain2
- Added `src/toolchain2/emit/profiles/swift.json`
- Added `src/runtime/swift/mapping.json`
- Added Swift emit/copy/build/run steps to `tools/check/runtime_parity_check_fast.py`
- Added `src/runtime/swift/image_runtime.swift`
- Added bootstrap-required helpers to `src/runtime/swift/built_in/py_runtime.swift`

## What was confirmed so far

- The Swift target can be launched from the parity harness
- `add`, `assign`, `alias_arg`, `class`, `class_instance`, `if_else`, `for_range`, `import_math_module` all PASS
- `collections` and `from_import_symbols` progress through emit/run; remaining work is container helper and output parity polish

## Remaining issues

- Fix return values and destructive updates for container mutation (`dict.pop`, `dict.setdefault`, set/list mutation)
- Eliminate the output mismatch in `from_import_symbols`
- Pass full-fixture parity
- Resolve the large volume of emitter hardcode lint violations in a separate task
