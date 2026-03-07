#include <chrono>

#include "runtime/cpp/generated/std/time.h"

namespace pytra::std::time {

float64 perf_counter() {
    using clock = ::std::chrono::steady_clock;
    const auto now = clock::now().time_since_epoch();
    return static_cast<float64>(
        ::std::chrono::duration_cast<::std::chrono::duration<double>>(now).count()
    );
}

}  // namespace pytra::std::time
