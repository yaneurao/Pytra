#ifndef PYTRA_BUILT_IN_FORMAT_OPS_H
#define PYTRA_BUILT_IN_FORMAT_OPS_H

#include <cstdio>
#include <string>
#include "core/py_types.h"

// py_fmt_int: format integer with Python format spec (e.g. "4d", "08d").
static inline str py_fmt_int(int64 v, const char* spec) {
    char buf[128];
    std::string fmt = std::string("%") + spec;
    // Replace trailing 'd' with 'l' 'd' for int64
    if (!fmt.empty() && fmt.back() == 'd') {
        fmt.back() = 'l';
        fmt += 'd';
    }
    ::std::snprintf(buf, sizeof(buf), fmt.c_str(), (long)v);
    return str(buf);
}

// py_fmt_float: format float with Python format spec (e.g. ".4f", "8.2f").
static inline str py_fmt_float(double v, const char* spec) {
    char buf[128];
    std::string fmt = std::string("%") + spec;
    ::std::snprintf(buf, sizeof(buf), fmt.c_str(), v);
    return str(buf);
}

// py_fmt_str: format string with Python format spec (e.g. "10s").
static inline str py_fmt_str(const str& v, const char* spec) {
    char buf[256];
    std::string fmt = std::string("%") + spec;
    if (!fmt.empty() && fmt.back() == 's') {
        ::std::snprintf(buf, sizeof(buf), fmt.c_str(), v.c_str());
    } else {
        return v;
    }
    return str(buf);
}

#endif  // PYTRA_BUILT_IN_FORMAT_OPS_H
