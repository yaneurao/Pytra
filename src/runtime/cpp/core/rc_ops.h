#ifndef PYTRA_CORE_RC_OPS_H
#define PYTRA_CORE_RC_OPS_H

#include <type_traits>
#include "core/py_types.h"

template <class T, ::std::enable_if_t<::std::is_arithmetic_v<T>, int> = 0>
static inline auto operator-(const rc<T>& v) -> decltype(v->__neg__()) {
    return v->__neg__();
}

#endif  // PYTRA_CORE_RC_OPS_H
