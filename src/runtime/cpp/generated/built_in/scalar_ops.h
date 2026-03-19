// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/built_in/scalar_ops.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_BUILT_IN_SCALAR_OPS_H
#define PYTRA_GEN_BUILT_IN_SCALAR_OPS_H

// forward declarations
int64 py_to_int64_base(const str& v, int64 base);
int64 py_ord(const str& ch);
str py_chr(int64 codepoint);

/* Extern-marked scalar helper built-ins. */

int64 py_to_int64_base(const str& v, int64 base) {
    return __b.py_int(v, base);
}

int64 py_ord(const str& ch) {
    return __b.ord(ch);
}

str py_chr(int64 codepoint) {
    return __b.chr(codepoint);
}

#endif  // PYTRA_GEN_BUILT_IN_SCALAR_OPS_H
