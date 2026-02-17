// このファイルは Python の `sys` モジュール互換の最小実装です。
// 現時点では、トランスパイル済みコードで使う `sys.path.insert` を提供します。

#ifndef PYCS_CPP_MODULE_SYS_H
#define PYCS_CPP_MODULE_SYS_H

#include <cstddef>
#include <string>
#include <vector>

namespace pytra::cpp_module {

/**
 * @brief Python の `sys.path` を模したコンテナです。
 */
class SysPath {
public:
    /**
     * @brief `sys.path.insert(index, value)` 相当の操作を行います。
     * @param index 挿入位置。範囲外の場合は末尾へ追加します。
     * @param value 追加するパス文字列。
     */
    void insert(int index, const std::string& value);

private:
    std::vector<std::string> entries_;
};

/**
 * @brief Python の `sys` モジュール相当オブジェクトです。
 */
class SysModule {
public:
    SysModule();
    ~SysModule();

    // Python 互換で `sys.path` として公開するメンバー。
    SysPath* path;
};

// グローバル `sys` オブジェクト。
extern SysModule* sys;

}  // namespace pytra::cpp_module

using pytra::cpp_module::sys;

#endif  // PYCS_CPP_MODULE_SYS_H
