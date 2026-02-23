#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_IMPL_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_IMPL_H

#include "runtime/cpp/pytra/built_in/py_runtime.h"

namespace pytra::std::dataclasses_impl {

// C++ ランタイム側では `@dataclass` は EAST 生成時に解決済みのため、
// 実行時には no-op 相当で十分。
inline object dataclass(
    const ::std::optional<object>& _cls = ::std::nullopt,
    bool init = true,
    bool repr = true,
    bool eq = true
) {
    (void)init;
    (void)repr;
    (void)eq;
    if (_cls.has_value()) {
        return _cls.value();
    }
    return make_object(::std::nullopt);
}

}  // namespace pytra::std::dataclasses_impl

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_DATACLASSES_IMPL_H
