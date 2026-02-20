#include "runtime/cpp/pytra/std/time-impl.h"

#include <chrono>

namespace pytra::std::time_impl {

double perf_counter() {
    using clock = ::std::chrono::steady_clock;
    const auto now = clock::now().time_since_epoch();
    return ::std::chrono::duration_cast<::std::chrono::duration<double>>(now).count();
}

}  // namespace pytra::std::time_impl

