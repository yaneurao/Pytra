// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: tools/gen_runtime_from_manifest.py

#ifndef PYTRA_GEN_STD_OS_H
#define PYTRA_GEN_STD_OS_H

// forward declarations
str getcwd();
void mkdir(const str& p);
void makedirs(const str& p, bool exist_ok = false);

/* pytra.std.os: extern-marked os subset with Python runtime fallback. */

str getcwd() {
    return __os.getcwd();
}

void mkdir(const str& p) {
    __os.mkdir(p);
}

void makedirs(const str& p, bool exist_ok = false) {
    __os.makedirs(p, exist_ok);
}

#endif  // PYTRA_GEN_STD_OS_H
