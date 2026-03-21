#include "core/py_runtime.h"
#include "core/process_runtime.h"

/* Pure-Python source-of-truth for sequence helpers used by runtime built-ins. */

list<int64> py_range(int64 start, int64 stop, int64 step) {
    rc<list<int64>> out = rc_list_from_value(list<int64>{});
    if (step == 0)
        return rc_list_copy_value(out);
    int64 i;
    if (step > 0) {
        i = start;
        while (i < stop) {
            rc_list_ref(out).append(i);
            i += step;
        }
    } else {
        i = start;
        while (i > stop) {
            rc_list_ref(out).append(i);
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
