// このファイルは Python 由来の補助モジュール（Path, sys, str など）を
// C++ 側で扱うための最小ランタイム実装です。

#ifndef PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
#define PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H

#include <cstdlib>
#include <stdexcept>
#include <string>
#include <vector>

#include "cpp_module/pathlib.h"

namespace pycs::cpp_module {

class SysPath {
public:
    /**
     * @brief sys.path への挿入を模した操作です。
     * @param index 挿入位置（範囲外なら末尾へ追加）
     * @param value 追加するパス文字列
     */
    void insert(int index, const std::string& value) {
        if (index < 0 || static_cast<std::size_t>(index) >= entries_.size()) {
            entries_.push_back(value);
            return;
        }
        entries_.insert(entries_.begin() + index, value);
    }

private:
    std::vector<std::string> entries_;
};

class SysModule {
public:
    SysModule() : path(new SysPath()) {}
    ~SysModule() { delete path; }

    SysPath* path;
};

inline SysModule* sys = new SysModule();

}  // namespace pycs::cpp_module

using pycs::cpp_module::sys;

#ifndef __file__
#define __file__ __FILE__
#endif

// Python側の transpile 呼び出しをC++から委譲するためのブリッジ。
/**
 * @brief C++ 側から Python 実装の transpile 関数を呼び出します。
 * @param input_path 入力Pythonファイルパス
 * @param output_path 出力C++ファイルパス
 */
inline void transpile(const std::string& input_path, const std::string& output_path) {
    std::string cmd =
        "python -c \"import sys;sys.path.insert(0,'.');from src.pycpp_transpiler import transpile;"
        "transpile(r'" +
        input_path + "', r'" + output_path + "')\"";
    std::system(cmd.c_str());
}

#endif  // PYCS_CPP_MODULE_PY_RUNTIME_MODULES_H
