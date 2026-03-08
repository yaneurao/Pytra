// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: src/backends/cpp/cli.py

#ifndef PYTRA_GENERATED_BUILT_IN_ZIP_OPS_H
#define PYTRA_GENERATED_BUILT_IN_ZIP_OPS_H

#include "runtime/cpp/core/py_runtime.h"


/* Pure-Python source-of-truth for generic zip helpers. */

template <class A, class B>
list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs) {
    rc<list<::std::tuple<A, B>>> out = rc_list_from_value(list<::std::tuple<A, B>>{});
    int64 i = 0;
    int64 n = py_len(lhs);
    if (py_len(rhs) < n)
        n = py_len(rhs);
    while (i < n) {
        py_append(out, ::std::make_tuple(lhs[i], rhs[i]));
        i++;
    }
    return rc_list_copy_value(out);
}

#endif  // PYTRA_GENERATED_BUILT_IN_ZIP_OPS_H
