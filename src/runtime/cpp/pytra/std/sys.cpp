// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/sys.py
// command: python3 tools/generate_cpp_pylib_runtime.py

#include "runtime/cpp/pytra/std/sys.h"

namespace pytra::cpp_module {

void SysPath::insert(int index, const std::string& value) {
    if (index < 0 || static_cast<std::size_t>(index) >= entries_.size()) {
        entries_.push_back(value);
        return;
    }
    entries_.insert(entries_.begin() + index, value);
}

SysModule::SysModule() : path(new SysPath()) {}

SysModule::~SysModule() {
    delete path;
}

SysModule* sys = new SysModule();

}  // namespace pytra::cpp_module
