// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/glob.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_GLOB_H
#define PYTRA_GEN_STD_GLOB_H

// forward declarations
list<str> glob(const str& pattern);

/* pytra.std.glob: extern-marked glob subset with Python runtime fallback. */

list<str> glob(const str& pattern) {
    return __glob.glob(pattern);
}

#endif  // PYTRA_GEN_STD_GLOB_H
