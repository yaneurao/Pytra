// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/zip_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_ZIP_OPS_H
#define PYTRA_GEN_BUILT_IN_ZIP_OPS_H

// forward declarations
list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs);

/* Pure-Python source-of-truth for generic zip helpers. */

template <class A, class B>
list<::std::tuple<A, B>> zip(const list<A>& lhs, const list<B>& rhs) {
    list<::std::tuple<A, B>> out = {};
    int64 i = 0;
    int64 n = lhs.size();
    if (rhs.size() < n)
        n = rhs.size();
    while (i < n) {
        out.append(::std::make_tuple(lhs[i], rhs[i]));
        i++;
    }
    return out;
}

#endif  // PYTRA_GEN_BUILT_IN_ZIP_OPS_H
