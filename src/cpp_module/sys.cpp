// このファイルは Python の `sys` モジュール互換実装の本体です。

#include "cpp_module/sys.h"

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
