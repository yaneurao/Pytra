#ifndef PYTRA_RUNTIME_CPP_BASE_BYTES_UTIL_H
#define PYTRA_RUNTIME_CPP_BASE_BYTES_UTIL_H

#include <cstdint>
#include <string>
#include <vector>

namespace pytra::runtime::cpp::base {

std::vector<std::uint8_t> int_to_bytes(std::int64_t value, std::int64_t length, const std::string& byteorder);

}  // namespace pytra::runtime::cpp::base

#endif  // PYTRA_RUNTIME_CPP_BASE_BYTES_UTIL_H
