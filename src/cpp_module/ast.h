// このファイルは Python の ast モジュール互換ランタイムです。
// 代表的な構文ノードをC++構造体で表現し、parse() で構文木を生成します。

#ifndef PYCS_CPP_MODULE_AST_H
#define PYCS_CPP_MODULE_AST_H

#include <memory>
#include <any>
#include <optional>
#include <string>
#include <type_traits>
#include <vector>

namespace pytra::cpp_module::ast {

struct expr;
struct stmt;
struct cmpop;
struct operator_;
struct keyword;

template <typename Base>
class PyPtr {
public:
    PyPtr() = default;
    PyPtr(std::nullptr_t) {}
    PyPtr(const std::shared_ptr<Base>& ptr) : ptr_(ptr) {}
    PyPtr(std::shared_ptr<Base>&& ptr) : ptr_(std::move(ptr)) {}
    template <typename Derived, typename = std::enable_if_t<std::is_base_of_v<Base, Derived>>>
    PyPtr(const std::shared_ptr<Derived>& ptr) : ptr_(std::static_pointer_cast<Base>(ptr)) {}

    Base* operator->() const { return ptr_.get(); }
    Base& operator*() const { return *ptr_; }
    explicit operator bool() const { return static_cast<bool>(ptr_); }
    bool operator==(std::nullptr_t) const { return ptr_ == nullptr; }
    bool operator!=(std::nullptr_t) const { return ptr_ != nullptr; }

    template <typename T>
    operator std::shared_ptr<T>() const {
        return std::dynamic_pointer_cast<T>(ptr_);
    }

    operator std::shared_ptr<Base>() const { return ptr_; }

private:
    std::shared_ptr<Base> ptr_;
};

struct Node {
    virtual ~Node() = default;
};

struct keyword : Node {
    std::string arg;
    PyPtr<expr> value;
};

struct expr : Node {
    // Python AST 互換のための汎用フィールド
    std::string id;
    std::string attr;
    PyPtr<expr> value;
    PyPtr<expr> left;
    PyPtr<expr> right;
    PyPtr<expr> operand;
    PyPtr<expr> func;
    PyPtr<expr> slice;
    std::vector<PyPtr<expr>> elts;
    std::vector<PyPtr<expr>> args;
    std::vector<PyPtr<expr>> values;
    std::vector<std::shared_ptr<cmpop>> ops;
    std::vector<PyPtr<expr>> comparators;
    std::shared_ptr<operator_> op;
    std::vector<std::shared_ptr<keyword>> keywords;
    virtual std::string as_text() const = 0;
};

struct RawExpr : expr {
    explicit RawExpr(std::string t) : text(std::move(t)) {}
    std::string text;
    std::string as_text() const override { return text; }
};

using ExprPtr = PyPtr<expr>;

struct operator_ : Node {};
struct unaryop : Node {};
struct boolop : Node {};
struct cmpop : Node {};

struct Add : operator_ {};
struct Sub : operator_ {};
struct Mult : operator_ {};
struct Div : operator_ {};
struct Mod : operator_ {};
struct BitOr : operator_ {};

struct UAdd : unaryop {};
struct USub : unaryop {};
struct Not : unaryop {};

struct And : boolop {};
struct Or : boolop {};

struct Eq : cmpop {};
struct NotEq : cmpop {};
struct Lt : cmpop {};
struct LtE : cmpop {};
struct Gt : cmpop {};
struct GtE : cmpop {};
struct In : cmpop {};
struct NotIn : cmpop {};
struct Is : cmpop {};
struct IsNot : cmpop {};

struct Name : expr {
    std::string id;
    std::string as_text() const override { return id; }
};

struct Constant : expr {
    std::any value;
    std::string repr;
    std::string as_text() const override { return repr; }
};

struct Attribute : expr {
    ExprPtr value;
    std::string attr;
    std::string as_text() const override { return (value ? value->as_text() : std::string()) + "." + attr; }
};

struct Tuple : expr {
    std::vector<ExprPtr> elts;
    std::string as_text() const override { return "tuple"; }
};

struct List : expr {
    std::vector<ExprPtr> elts;
    std::string as_text() const override { return "list"; }
};

struct Set : expr {
    std::vector<ExprPtr> elts;
    std::string as_text() const override { return "set"; }
};

struct Dict : expr {
    std::vector<ExprPtr> keys;
    std::vector<ExprPtr> values;
    std::string as_text() const override { return "dict"; }
};

struct BinOp : expr {
    ExprPtr left;
    std::shared_ptr<operator_> op;
    ExprPtr right;
    std::string as_text() const override { return "binop"; }
};

struct UnaryOp : expr {
    std::shared_ptr<unaryop> op;
    ExprPtr operand;
    std::string as_text() const override { return "unaryop"; }
};

struct BoolOp : expr {
    std::shared_ptr<boolop> op;
    std::vector<ExprPtr> values;
    std::string as_text() const override { return "boolop"; }
};

struct Compare : expr {
    ExprPtr left;
    std::vector<std::shared_ptr<cmpop>> ops;
    std::vector<ExprPtr> comparators;
    std::string as_text() const override { return "compare"; }
};

struct Call : expr {
    ExprPtr func;
    std::vector<ExprPtr> args;
    std::vector<std::shared_ptr<keyword>> keywords;
    std::string as_text() const override { return "call"; }
};

struct Subscript : expr {
    ExprPtr value;
    ExprPtr slice;
    std::string as_text() const override { return "subscript"; }
};

struct IfExp : expr {
    ExprPtr test;
    ExprPtr body;
    ExprPtr orelse;
    std::string as_text() const override { return "ifexp"; }
};

struct FormattedValue : expr {
    ExprPtr value;
    std::string as_text() const override { return "formatted"; }
};

struct JoinedStr : expr {
    std::vector<ExprPtr> values;
    std::string as_text() const override { return "joinedstr"; }
};

struct ListComp : expr {
    std::string as_text() const override { return "listcomp"; }
};
struct SetComp : expr {
    std::string as_text() const override { return "setcomp"; }
};
struct GeneratorExp : expr {
    std::string as_text() const override { return "genexp"; }
};

struct stmt : Node {
    // Python AST 互換のための汎用フィールド
    std::string name;
    struct PyStr {
        std::string v;
        PyStr() = default;
        PyStr(const std::string& s) : v(s) {}
        PyStr(const char* s) : v(s) {}
        operator std::string() const { return v; }
        explicit operator bool() const { return !v.empty(); }
        bool operator==(std::nullptr_t) const { return v.empty(); }
        bool operator!=(std::nullptr_t) const { return !v.empty(); }
    };
    PyStr module;
    PyPtr<expr> value;
    PyPtr<expr> target;
    PyPtr<expr> iter;
    PyPtr<expr> test;
    PyPtr<expr> annotation;
    std::vector<PyPtr<expr>> targets;
    std::vector<PyPtr<stmt>> body;
    std::vector<PyPtr<stmt>> orelse;
    std::vector<PyPtr<stmt>> finalbody;
    std::vector<std::shared_ptr<Node>> handlers;
    std::vector<ExprPtr> decorator_list;
    virtual ~stmt() = default;
};

using StmtPtr = PyPtr<stmt>;

struct ImportAlias {
    std::string name;
    std::string asname;
};

struct Import : stmt {
    std::vector<std::shared_ptr<ImportAlias>> names;
};

struct ImportFrom : stmt {
    PyStr module;
    std::vector<std::shared_ptr<ImportAlias>> names;
};

struct Pass : stmt {};
struct Break : stmt {};
struct Continue : stmt {};

struct ExprStmt : stmt {
    ExprPtr value;
};
using Expr = ExprStmt;
using Expr = ExprStmt;

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
    ExprPtr value;
};

struct Raise : stmt {
    ExprPtr exc;
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

struct ExceptHandler : Node {
    ExprPtr type;
    std::string name;
    std::vector<StmtPtr> body;
};

struct Try : stmt {
    std::vector<StmtPtr> body;
    std::vector<std::shared_ptr<ExceptHandler>> handlers;
    std::vector<StmtPtr> finalbody;
};

struct arg : Node {
    std::string arg;
    ExprPtr annotation;
};

struct arguments : Node {
    std::vector<std::shared_ptr<arg>> args;
};

struct FunctionDef : stmt {
    std::string name;
    std::shared_ptr<arguments> args;
    ExprPtr returns;
    std::vector<std::string> decorators;
    std::vector<StmtPtr> body;
};

struct ClassDef : stmt {
    std::string name;
    std::string base;
    std::vector<ExprPtr> bases;
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

}  // namespace pytra::cpp_module::ast

#endif  // PYCS_CPP_MODULE_AST_H
