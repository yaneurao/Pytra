// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/runtime/std/sys.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#ifndef PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H
#define PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H

#include <cstddef>
#include <string>
#include <vector>

namespace pytra::cpp_module {

class SysPath {
public:
    void insert(int index, const std::string& value);

private:
    std::vector<std::string> entries_;
};

class SysModule {
public:
    SysModule();
    ~SysModule();

    SysPath* path;
};

extern SysModule* sys;

}  // namespace pytra::cpp_module

using pytra::cpp_module::sys;

#endif  // PYTRA_RUNTIME_CPP_PYTRA_STD_SYS_H
