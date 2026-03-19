// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/sequence.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_SEQUENCE_H
#define PYTRA_GEN_BUILT_IN_SEQUENCE_H

// forward declarations
list<int64> py_range(int64 start, int64 stop, int64 step);
str py_repeat(const str& v, int64 n);

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

#endif  // PYTRA_GEN_BUILT_IN_SEQUENCE_H
