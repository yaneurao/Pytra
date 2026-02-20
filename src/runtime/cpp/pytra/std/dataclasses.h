// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/dataclasses.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H

#include <type_traits>

namespace pytra::cpp_module::dataclasses {

struct DataclassTag {};

template <typename T>
constexpr T dataclass(T value) {
    return value;
}

template <typename T>
constexpr bool is_dataclass_v = std::is_base_of_v<DataclassTag, T>;

}  // namespace pytra::cpp_module::dataclasses

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_H
