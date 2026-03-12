// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/native/core/py_runtime.h"

#include "runtime/cpp/generated/built_in/sequence.h"
#include "runtime/cpp/native/core/process_runtime.h"
#include "runtime/cpp/native/core/scope_exit.h"


/* Pure-Python source-of-truth for sequence helpers used by runtime built-ins. */

list<int64> py_range(int64 start, int64 stop, int64 step) {
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    if (step == 0)
        return rc_list_copy_value(out);
    int64 i;
    if (step > 0) {
        i = start;
        while (i < stop) {
            py_list_append_mut(rc_list_ref(out), i);
            i += step;
        }
    } else {
        i = start;
        while (i > stop) {
            py_list_append_mut(rc_list_ref(out), i);
            i += step;
        }
    }
    return rc_list_copy_value(out);
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
