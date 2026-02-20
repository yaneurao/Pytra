// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/time.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include <chrono>

#include "runtime/cpp/pytra/std/time.h"

namespace pytra::cpp_module {

double perf_counter() {
    using Clock = ::std::chrono::steady_clock;
    using Seconds = ::std::chrono::duration<double>;
    return Seconds(Clock::now().time_since_epoch()).count();
}

}  // namespace pytra::cpp_module
