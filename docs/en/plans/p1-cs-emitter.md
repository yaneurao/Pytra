<a href="../../ja/plans/p1-cs-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-CS-EMITTER: Implement a new C# emitter in toolchain2

Last updated: 2026-03-31
Status: In progress (S3/S4/S5 completed, S6 not started)

## Background

C# is widely used in Unity and the .NET ecosystem, and there is high user demand for it as a Pytra target language. A C# emitter (`src/toolchain/emit/cs/`) and runtime (`src/runtime/cs/`) exist in the old toolchain1, but they need to be migrated to the new toolchain2 pipeline.

## Design

### Emitter structure

- Implemented in `src/toolchain2/emit/cs/` using CommonRenderer + override structure
- Reference the old `src/toolchain/emit/cs/` and TS emitter (`src/toolchain2/emit/ts/`)
- Only override nodes specific to C# (namespace, using, property, LINQ, nullable types, etc.)

### mapping.json

Define the following in `src/runtime/cs/mapping.json`:
- `calls`: runtime_call mappings
- `types`: EAST3 type names → C# type names (`int64` → `long`, `float64` → `double`, `str` → `string`, `Exception` → `Exception`, etc.)
- `env.target`: `"\"cs\""`
- `builtin_prefix`: `"py_"`
- `implicit_promotions`: C# implicit promotion pairs (nearly the same as C++)

### parity check

- The emit path for `pytra-cli2 -build --target cs` is supported. compile + run parity not yet started.
- Verify with `runtime_parity_check_fast.py --targets cs`
- Three stages: fixture + sample + stdlib

## Decision Log

- 2026-03-30: C# backend role established. Approach: implement toolchain2 emitter following the emitter guide.
- 2026-03-30: Created `src/toolchain2/emit/cs/` and added `emit_cs_module()` / `types.py` / `toolchain2/emit/profiles/cs.json`. Created `src/runtime/cs/mapping.json` and connected the `pytra-cli2 --target cs` emit/build path to the toolchain2 emitter.
- 2026-03-30: Per emitter guide §13, C#-specific checker is withdrawn and `tools/check/runtime_parity_check_fast.py` is adopted as the canonical path. `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category core` passes 22/22.
- 2026-03-30: Expanded C# emitter/runtime for `collections` / `control`. Implemented container method lowering, Python-compatible `and` / `or`, membership, slice, list repeat, comprehension, try/finally, nested closure, exception display. `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category collections` passes 20/20, `--category control` passes 16/16.
- 2026-03-30: Expanded C# emitter for `imports` / `oop`. Implemented C#-specific resolution of runtime import bindings, module attr lowering, `bytes` / `bytearray` ctor and mutation, trait → interface output, `@staticmethod`, dataclass ctor generation, linked EAST3 `pytra_isinstance` / `ObjTypeId` call rendering, `super().method()`, `virtual` / `override`. Confirmed `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category imports` passes 7/7, `--category oop` passes 18/18. Full fixture not yet achieved; remaining gaps at that point: `--category signature` 5/13, `--category strings` 6/12, `--category typing` 8/23.
- 2026-03-30: Additional fixes to C# emitter/runtime for `strings` / `signature`. Added `VarDecl`, hoisted loop target, tuple target comprehension, list concat, mixed-type equality, `yields_dynamic` / `Unbox` cast, `type(v).__name__`, string iteration, `sum` / `zip` / `enumerate` / `reversed` / `index` / `strip` / `rstrip` / `startswith` / `endswith` / `replace` helpers, sequence display. Improved `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category strings` to 12/12. Remaining gaps: `--category signature` 8/13, `--category typing` 8/23.
- 2026-03-30: Additional fixes for `signature` / `typing` / remaining fixtures. Added format spec f-string, `Swap`, typed varargs, straightforward rendering of linked EAST3 `pytra_isinstance`, `JsonVal` narrowing cast, type-id constant resolution, user-defined class type registration, POD exact `isinstance`, `Any` dict boxing, subscript assignment, small integer promotion cast, `deque` runtime. Confirmed `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --category signature` passes 13/13, `--category typing` passes 23/23. Full fixture sweep: 130/131 pass + 1 temporary runtime copy error in `import_time_from`; that case alone and `--category imports` pass on re-run.
- 2026-03-31: Re-applied C# fixes lost due to stash regression to `src/toolchain2/emit/cs/emitter.py` / `src/runtime/cs/`. Restored linked EAST3 `pytra_isinstance`, `type_id_resolved_v1`, `yields_dynamic`, enum constants, Python `/` and `//`, sample-targeted `min` / `max`, negative-step range, subscript swap. Reached `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs` fixture 131/131 pass.
- 2026-03-31: Continued sample parity. Fixed a path where `typing.cast` in `pytra.std.pathlib` was incorrectly lowered to `Typing.cast(...)` via `build_import_alias_map()`. Made the C# emitter render `cast` in Name calls as a no-op cast before import alias resolution. Individually swept 18 samples and confirmed 18/18 pass.
- 2026-04-01: Alongside `P2-CS-LINT-S1`, reviewed the C# parity checker execution path. Added `dotnet` fallback to `tools/check/runtime_parity_check_fast.py` and C#-specific `can_run()` fallback to `tools/check/runtime_parity_check.py`. Also reinforced C# emitter/runtime with `Path` type resolution, optional nominal type module qualification, cast parentheses, module-level function qualification, loop target alias, and `py_runtime.index(string, string)`. Confirmed `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets cs --case-root stdlib` passes 16/16.
