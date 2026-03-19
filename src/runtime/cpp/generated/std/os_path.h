// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os_path.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_OS_PATH_H
#define PYTRA_GEN_STD_OS_PATH_H

// forward declarations
str join(const str& a, const str& b);
str dirname(const str& p);
str basename(const str& p);
str abspath(const str& p);
bool exists(const str& p);

/* pytra.std.os_path: extern-marked os.path subset with Python runtime fallback. */

str join(const str& a, const str& b) {
    return __path.join(a, b);
}

str dirname(const str& p) {
    return __path.dirname(p);
}

str basename(const str& p) {
    return __path.basename(p);
}

::std::tuple<str, str> splitext(const str& p) {
    return __path.splitext(p);
}

str abspath(const str& p) {
    return __path.abspath(p);
}

bool exists(const str& p) {
    return __path.exists(p);
}

#endif  // PYTRA_GEN_STD_OS_PATH_H
