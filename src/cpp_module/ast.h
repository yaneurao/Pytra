// このファイルは Python の ast モジュール互換の最小スタブです。
// 将来的な拡張を想定してノード基底型と parse API を提供します。

#ifndef PYCS_CPP_MODULE_AST_H
#define PYCS_CPP_MODULE_AST_H

#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace pycs::cpp_module::ast {

struct Node {
    virtual ~Node() = default;
};

struct stmt : Node {};
struct expr : Node {};

struct Module : Node {
    std::vector<std::shared_ptr<stmt>> body;
};

struct Name : expr {
    std::string id;
};

struct Constant : expr {
    std::string repr;
};

// 注意:
// 本関数は将来の完全実装用の入口です。現時点では構文木生成は未実装です。
inline std::shared_ptr<Module> parse(const std::string& /*source*/, const std::string& /*filename*/ = "<unknown>") {
    throw std::runtime_error("cpp_module::ast::parse is not implemented yet");
}

}  // namespace pycs::cpp_module::ast

#endif  // PYCS_CPP_MODULE_AST_H
