# P0 C++ object seam inventory

Last updated: 2026-04-02

## Purpose

Before removing `Object<void>` / `using object = Object<void>` from `src/runtime/cpp/core/object.h`, take inventory of all object seams remaining in the C++ backend and fix which TODO will remove each one.

## Current seams

### 1. EAST / lower origin

- `src/toolchain2/compile/lower.py`
  - `resolved_type="object"` boxing
  - iter boundary (`OBJ_ITER_INIT`, `OBJ_ITER_NEXT`)
  - Conversion table to `PYTRA_TID_OBJECT`

Owner:
- `P0-CPP-VARIANT-S10`
- `P0-CPP-VARIANT-S11`

### 2. C++ emitter origin

- `src/toolchain2/emit/cpp/emitter.py`
  - `Box` / `Unbox` emission
  - `object(...)` boxing path
  - `.as<...>()` / `.unbox<...>()`
  - Generic `Callable` bridge `([&](object) -> object { ... })`
  - Object fallback containers (`dict[str, object]`, `list[object]`, `set[object]`)
  - Object-based type narrowing / cast fallback

Owner:
- `P0-CPP-VARIANT-S8`
- `P0-CPP-VARIANT-S9`
- `P0-CMN-BOXUNBOX-S1`
- `P0-CMN-BOXUNBOX-S2`

### 3. C++ runtime stdlib seam

- `src/runtime/cpp/std/argparse.{h,cpp}`
  - `Namespace.values: Object<dict<str, object>>`
  - `default_value: object`
- `src/runtime/cpp/std/pathlib.{h,cpp}`
  - `Path(const object&)`
  - `__truediv__(const object&)`
  - `relative_to(const object&)`
- Tuple runtime fallback
  - `src/runtime/cpp/built_in/dict_ops.h`
  - `py_at(tuple, idx) -> object`

Owner:
- `P0-CPP-VARIANT-S8`
- File a separate ticket if the object-free signature migration for runtime stdlib needs to be tracked independently

### 4. Runtime core seam

- `src/runtime/cpp/core/object.h`
  - `Object<void>`
  - `using object = Object<void>`
- `src/runtime/cpp/core/py_types.h`
  - `Object<void>::unbox`
  - POD boxing constructors
- `src/runtime/cpp/built_in/base_ops.h`
  - `py_is_*` / `py_to_string(const object&)`
- `src/runtime/cpp/core/conversions.h`
  - `py_to_int64(const object&)`, `py_to_float64(const object&)`, etc.

Owner:
- `P0-CPP-VARIANT-S6B`

## Removal order

1. `P0-CMN-BOXUNBOX-S1/S2`: introduce shared normalization in CommonRenderer
2. `P0-CPP-VARIANT-S8/S9`: reduce C++ emitter dependency on object boxing / unboxing
3. `P0-CPP-VARIANT-S10/S11`: stop object degradation on the EAST side
4. Confirm that runtime stdlib seams pass without object
5. `P0-CPP-VARIANT-S6B`: delete the `object.h` body

## Completion Criteria

- Each seam listed above is tied one-to-one to a TODO ID
- What must be done before deleting `object.h` can be determined from TODOs alone
