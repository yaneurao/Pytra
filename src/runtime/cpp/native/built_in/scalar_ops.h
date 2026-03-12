#ifndef PYTRA_NATIVE_BUILT_IN_SCALAR_OPS_H
#define PYTRA_NATIVE_BUILT_IN_SCALAR_OPS_H

#include "runtime/cpp/generated/built_in/scalar_ops.h"
#include "runtime/cpp/native/core/py_runtime.h"

inline int64 py_to_int64_base(const str& v, int64 base) {
    int b = static_cast<int>(base);
    if (b < 2 || b > 36) b = 10;
    return static_cast<int64>(::std::stoll(static_cast<::std::string>(v), nullptr, b));
}

inline int64 py_to_int64_base(const ::std::string& v, int64 base) {
    return py_to_int64_base(str(v), base);
}

inline int64 py_to_int64_base(const object& v, int64 base) {
    return py_to_int64_base(obj_to_str(v), base);
}

inline int64 py_ord(const str& ch) {
    const ::std::string& s = ch;
    if (s.empty()) return 0;
    const auto b0 = static_cast<unsigned char>(s[0]);
    if ((b0 & 0x80) == 0) return static_cast<int64>(b0);
    if ((b0 & 0xE0) == 0xC0 && s.size() >= 2) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        return static_cast<int64>(((b0 & 0x1F) << 6) | (b1 & 0x3F));
    }
    if ((b0 & 0xF0) == 0xE0 && s.size() >= 3) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        const auto b2 = static_cast<unsigned char>(s[2]);
        return static_cast<int64>(((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (b2 & 0x3F));
    }
    if ((b0 & 0xF8) == 0xF0 && s.size() >= 4) {
        const auto b1 = static_cast<unsigned char>(s[1]);
        const auto b2 = static_cast<unsigned char>(s[2]);
        const auto b3 = static_cast<unsigned char>(s[3]);
        return static_cast<int64>(((b0 & 0x07) << 18) | ((b1 & 0x3F) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F));
    }
    return static_cast<int64>(b0);
}

inline int64 py_ord(const object& v) {
    return py_ord(obj_to_str(v));
}

inline str py_chr(int64 codepoint) {
    int64 cp = codepoint;
    if (cp < 0) cp = 0;
    if (cp > 0x10FFFF) cp = 0x10FFFF;
    ::std::string out;
    if (cp <= 0x7F) {
        out.push_back(static_cast<char>(cp));
    } else if (cp <= 0x7FF) {
        out.push_back(static_cast<char>(0xC0 | ((cp >> 6) & 0x1F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else if (cp <= 0xFFFF) {
        out.push_back(static_cast<char>(0xE0 | ((cp >> 12) & 0x0F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else {
        out.push_back(static_cast<char>(0xF0 | ((cp >> 18) & 0x07)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
    return str(out);
}

inline str py_chr(const object& v) {
    return py_chr(obj_to_int64(v));
}

#endif  // PYTRA_NATIVE_BUILT_IN_SCALAR_OPS_H
