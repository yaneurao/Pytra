// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/built_in/sequence.h"


/* Pure-Python source-of-truth for sequence helpers used by runtime built-ins. */

list<int64> py_range(int64 start, int64 stop, int64 step) {
    list<int64> out = {};
    if (step == 0)
        return out;
    int64 i;
    if (step > 0) {
        i = start;
        while (i < stop) {
            out.append(i);
            i += step;
        }
    } else {
        i = start;
        while (i > stop) {
            out.append(i);
            i += step;
        }
    }
    return out;
}

str py_repeat(const str& v, int64 n) {
    if (n <= 0)
        return "";
    str out = "";
    int64 i = 0;
    while (i < n) {
        out += v;
        i++;
    }
    return out;
}
