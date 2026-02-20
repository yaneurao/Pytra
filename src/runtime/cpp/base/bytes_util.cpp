#include "runtime/cpp/base/bytes_util.h"

#include <stdexcept>

namespace pytra::runtime::cpp::base {

::std::vector<::std::uint8_t> int_to_bytes(::std::int64_t value, ::std::int64_t length, const ::std::string& byteorder) {
    if (length < 0) {
        throw ::std::runtime_error("to_bytes: length must be >= 0");
    }
    ::std::vector<::std::uint8_t> out(static_cast<::std::size_t>(length), 0);
    for (::std::int64_t i = 0; i < length; ++i) {
        ::std::uint8_t b = static_cast<::std::uint8_t>((static_cast<::std::uint64_t>(value) >> (8 * i)) & 0xFFu);
        if (byteorder == "little") {
            out[static_cast<::std::size_t>(i)] = b;
        } else if (byteorder == "big") {
            out[static_cast<::std::size_t>(length - 1 - i)] = b;
        } else {
            throw ::std::runtime_error("to_bytes: byteorder must be 'little' or 'big'");
        }
    }
    return out;
}

}  // namespace pytra::runtime::cpp::base
