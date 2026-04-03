<a href="../../en/plans/p10-cpp-typetable-redesign.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P10-CPP-TYPETABLE-REDESIGN

## Background

The `g_type_table` in `src/runtime/cpp/core/object.h` had been retained solely to look up a deleter when destroying `Object<T>`. Meanwhile, `isinstance` / `issubclass` checks for user classes were handled entirely by the `id_table` in generated `built_in/type_id.*` and `py_runtime_object_type_id(...)`, making the design where the toolchain2 C++ emitter calls `py_tid_register_known_class_type(...)` in each module a case of dual management.

## Inventory

- The only real uses of `g_type_table` were destructor dispatch in `Object<T>::release()` / `Object<void>::release()` and unit test initialization.
- The only real use of `py_tid_register_known_class_type(...)` was as a local helper emitted by the toolchain2 C++ emitter.
- `PYTRA_TID_*` is used widely as runtime constants for built-in scalars/containers/objects, so it is not included in the P10 removal targets.

## Design

- Give `ControlBlock` a `void (*deleter)(void*)` field and bake in the concrete type's deleter in `make_object<T>` and the POD boxing constructor.
- `Object<T>` / `Object<void>` `release()` calls `cb->deleter` directly. This makes the global type table unnecessary.
- Use the generated `id_table` as the source of truth for user class subtype checks, and remove the local `py_tid_register_known_class_type(...)` helper from the toolchain2 emitter.
- Remove dead known-registration APIs from `pytra.built_in.type_id` and `core/type_id_support.h`.

## Verification

- Targeted unit tests:
  - `tools/unittest/emit/cpp/test_object_t.py`
  - `tools/unittest/emit/cpp/test_cpp_runtime_type_id.py`
  - `tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- Parity:
  - `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2`
  - `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root sample --east3-opt-level 2`

## Results

- `tools/unittest/emit/cpp/test_object_t.py`: PASS
- `PYTRA_GENERATED_CPP_DIR=/workspace/Pytra/work/tmp/p10_typetable/class_instance_emit python3 tools/unittest/emit/cpp/test_cpp_runtime_type_id.py`: PASS
- Confirmed that local `__pytra_ensure_local_type_ids_*` helpers and `py_tid_register_known_class_type(...)` calls are absent from the C++ build of `class_instance.py` / `isinstance_user_class.py`
- `runtime_parity_check_fast.py`:
  - fixture `131/131 PASS`
  - sample `18/18 PASS`
