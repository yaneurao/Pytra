// このファイルは Python の ast モジュール互換ランタイムです。
// 代表的な構文ノードをC++構造体で表現し、parse() で構文木を生成します。

#ifndef PYCS_CPP_MODULE_AST_H
#define PYCS_CPP_MODULE_AST_H

#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace pycs::cpp_module::ast {

struct Node {
    virtual ~Node() = default;
};

struct expr : Node {
    virtual std::string as_text() const = 0;
};

struct RawExpr : expr {
    explicit RawExpr(std::string t) : text(std::move(t)) {}
    std::string text;
    std::string as_text() const override { return text; }
};

using ExprPtr = std::shared_ptr<expr>;

struct stmt : Node {
    virtual ~stmt() = default;
};

using StmtPtr = std::shared_ptr<stmt>;

struct ImportAlias {
    std::string name;
    std::string asname;
};

struct Import : stmt {
    std::vector<ImportAlias> names;
};

struct ImportFrom : stmt {
    std::string module;
    std::vector<ImportAlias> names;
};

struct Pass : stmt {};
struct Break : stmt {};
struct Continue : stmt {};

struct ExprStmt : stmt {
    ExprPtr value;
};

struct Assign : stmt {
    std::vector<ExprPtr> targets;
    ExprPtr value;
};

struct AnnAssign : stmt {
    ExprPtr target;
    ExprPtr annotation;
    std::optional<ExprPtr> value;
};

struct Return : stmt {
    std::optional<ExprPtr> value;
};

struct Raise : stmt {
    std::optional<ExprPtr> exc;
};

struct If : stmt {
    ExprPtr test;
    std::vector<StmtPtr> body;
    std::vector<StmtPtr> orelse;
};

struct For : stmt {
    ExprPtr target;
    ExprPtr iter;
    std::vector<StmtPtr> body;
    std::vector<StmtPtr> orelse;
};

struct ExceptHandler {
    std::string type;
    std::string name;
    std::vector<StmtPtr> body;
};

struct Try : stmt {
    std::vector<StmtPtr> body;
    std::vector<ExceptHandler> handlers;
    std::vector<StmtPtr> finalbody;
};

struct Arg {
    std::string arg;
    std::string annotation;
    std::string default_value;
};

struct FunctionDef : stmt {
    std::string name;
    std::vector<Arg> args;
    std::string returns;
    std::vector<std::string> decorators;
    std::vector<StmtPtr> body;
};

struct ClassDef : stmt {
    std::string name;
    std::string base;
    std::vector<std::string> decorators;
    std::vector<StmtPtr> body;
};

struct Module : Node {
    std::vector<StmtPtr> body;
};

using ModulePtr = std::shared_ptr<Module>;

// Pythonソース文字列を簡易ASTへ変換します。
ModulePtr parse(const std::string& source, const std::string& filename = "<unknown>");

// ファイルからPythonソースを読み込み、簡易ASTへ変換します。
ModulePtr parse_file(const std::string& path);

}  // namespace pycs::cpp_module::ast

#endif  // PYCS_CPP_MODULE_AST_H
