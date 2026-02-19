// このファイルは Python の `time` モジュール互換実装の本体です。

#include <chrono>

#include "runtime/cpp/pytra/std/time.h"

namespace pytra::cpp_module {

double perf_counter() {
    using Clock = std::chrono::steady_clock;
    using Seconds = std::chrono::duration<double>;
    return Seconds(Clock::now().time_since_epoch()).count();
}

}  // namespace pytra::cpp_module
