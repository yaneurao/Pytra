#include "core/py_runtime.h"
#include "core/process_runtime.h"
#include "built_in/scalar_ops.h"

/* Extern-marked scalar helper built-ins. */

int64 py_to_int64_base(const str& v, int64 base) {
    return py_to_int64_base(v, int64(base));
}

int64 py_ord(const str& ch) {
    return py_ord(ch);
}

str py_chr(int64 codepoint) {
    return py_chr(codepoint);
}
