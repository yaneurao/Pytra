// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/os.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_STD_OS_H
#define PYTRA_STD_OS_H

namespace pytra::std::os {

struct _PathModule;

extern _PathModule path;

str getcwd();
void mkdir(const str& p);
void makedirs(const str& p, bool exist_ok = false);

}  // namespace pytra::std::os

#endif  // PYTRA_STD_OS_H
