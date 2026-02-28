#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/dataclasses.h"
#include "pytra/std/time.h"

struct Token : public PyObj {
    str kind;
    str text;
    int64 pos;
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 py_type_id() const noexcept override {
        return PYTRA_TYPE_ID;
    }
    virtual bool py_isinstance_of(uint32 expected_type_id) const override {
        return expected_type_id == PYTRA_TYPE_ID;
    }
    
    Token(str kind, str text, int64 pos) {
        this->kind = kind;
        this->text = text;
        this->pos = pos;
    }
    
};

struct ExprNode : public PyObj {
    str kind;
    int64 value;
    str name;
    str op;
    int64 left;
    int64 right;
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 py_type_id() const noexcept override {
        return PYTRA_TYPE_ID;
    }
    virtual bool py_isinstance_of(uint32 expected_type_id) const override {
        return expected_type_id == PYTRA_TYPE_ID;
    }
    
    ExprNode(str kind, int64 value, str name, str op, int64 left, int64 right) {
        this->kind = kind;
        this->value = value;
        this->name = name;
        this->op = op;
        this->left = left;
        this->right = right;
    }
    
};

struct StmtNode : public PyObj {
    str kind;
    str name;
    int64 expr_index;
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 py_type_id() const noexcept override {
        return PYTRA_TYPE_ID;
    }
    virtual bool py_isinstance_of(uint32 expected_type_id) const override {
        return expected_type_id == PYTRA_TYPE_ID;
    }
    
    StmtNode(str kind, str name, int64 expr_index) {
        this->kind = kind;
        this->name = name;
        this->expr_index = expr_index;
    }
    
};

object tokenize(const object& lines) {
    object tokens = make_object(list<object>{});
    for (const auto& [line_index, source] : py_enumerate(py_to_str_list_from_object(lines))) {
        int64 i = 0;
        int64 n = py_len(source);
        while (i < n) {
            str ch = source[i];
            
            if (ch == " ") {
                i++;
                continue;
            }
            if (ch == "+") {
                py_append(tokens, make_object(::rc_new<Token>("PLUS", ch, i)));
                i++;
                continue;
            }
            if (ch == "-") {
                py_append(tokens, make_object(::rc_new<Token>("MINUS", ch, i)));
                i++;
                continue;
            }
            if (ch == "*") {
                py_append(tokens, make_object(::rc_new<Token>("STAR", ch, i)));
                i++;
                continue;
            }
            if (ch == "/") {
                py_append(tokens, make_object(::rc_new<Token>("SLASH", ch, i)));
                i++;
                continue;
            }
            if (ch == "(") {
                py_append(tokens, make_object(::rc_new<Token>("LPAREN", ch, i)));
                i++;
                continue;
            }
            if (ch == ")") {
                py_append(tokens, make_object(::rc_new<Token>("RPAREN", ch, i)));
                i++;
                continue;
            }
            if (ch == "=") {
                py_append(tokens, make_object(::rc_new<Token>("EQUAL", ch, i)));
                i++;
                continue;
            }
            if (ch.isdigit()) {
                int64 start = i;
                while ((i < n) && (source[i].isdigit())) {
                    i++;
                }
                str text = py_slice(source, start, i);
                py_append(tokens, make_object(::rc_new<Token>("NUMBER", text, start)));
                continue;
            }
            if ((ch.isalpha()) || (ch == "_")) {
                int64 start = i;
                while ((i < n) && (((source[i].isalpha()) || (source[i] == "_")) || (source[i].isdigit()))) {
                    i++;
                }
                str text = py_slice(source, start, i);
                if (text == "let") {
                    py_append(tokens, make_object(::rc_new<Token>("LET", text, start)));
                } else {
                    if (text == "print")
                        py_append(tokens, make_object(::rc_new<Token>("PRINT", text, start)));
                    else
                        py_append(tokens, make_object(::rc_new<Token>("IDENT", text, start)));
                }
                continue;
            }
            throw ::std::runtime_error("tokenize error at line=" + ::std::to_string(line_index) + " pos=" + ::std::to_string(i) + " ch=" + ch);
        }
        py_append(tokens, make_object(::rc_new<Token>("NEWLINE", "", n)));
    }
    py_append(tokens, make_object(::rc_new<Token>("EOF", "", py_len(lines))));
    return tokens;
}

struct Parser : public PyObj {
    object expr_nodes;
    int64 pos;
    object tokens;
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 py_type_id() const noexcept override {
        return PYTRA_TYPE_ID;
    }
    virtual bool py_isinstance_of(uint32 expected_type_id) const override {
        return expected_type_id == PYTRA_TYPE_ID;
    }
    
    object new_expr_nodes() {
        return make_object(list<object>{});
    }
    Parser(const object& tokens) {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    str peek_kind() {
        return obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos)), "subscript:list")->kind;
    }
    bool match(const str& kind) {
        if (this->peek_kind() == kind) {
            this->pos++;
            return true;
        }
        return false;
    }
    rc<Token> expect(const str& kind) {
        if (this->peek_kind() != kind) {
            rc<Token> t = obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos)), "subscript:list");
            throw ::std::runtime_error("parse error at pos=" + py_to_string(t->pos) + ", expected=" + kind + ", got=" + t->kind);
        }
        rc<Token> token = obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos)), "subscript:list");
        this->pos++;
        return token;
    }
    void skip_newlines() {
        while (this->match("NEWLINE")) {
            ;
        }
    }
    int64 add_expr(const rc<ExprNode>& node) {
        py_append(this->expr_nodes, make_object(node));
        return py_len(this->expr_nodes) - 1;
    }
    object parse_program() {
        object stmts = make_object(list<object>{});
        this->skip_newlines();
        while (this->peek_kind() != "EOF") {
            rc<StmtNode> stmt = this->parse_stmt();
            py_append(stmts, make_object(stmt));
            this->skip_newlines();
        }
        return stmts;
    }
    rc<StmtNode> parse_stmt() {
        if (this->match("LET")) {
            str let_name = py_to_string(this->expect("IDENT")->text);
            this->expect("EQUAL");
            int64 let_expr_index = this->parse_expr();
            return ::rc_new<StmtNode>("let", let_name, let_expr_index);
        }
        if (this->match("PRINT")) {
            int64 print_expr_index = this->parse_expr();
            return ::rc_new<StmtNode>("print", "", print_expr_index);
        }
        str assign_name = py_to_string(this->expect("IDENT")->text);
        this->expect("EQUAL");
        int64 assign_expr_index = this->parse_expr();
        return ::rc_new<StmtNode>("assign", assign_name, assign_expr_index);
    }
    int64 parse_expr() {
        return this->parse_add();
    }
    int64 parse_add() {
        int64 left = this->parse_mul();
        while (true) {
            if (this->match("PLUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(::rc_new<ExprNode>("bin", 0, "", "+", left, right));
                continue;
            }
            if (this->match("MINUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(::rc_new<ExprNode>("bin", 0, "", "-", left, right));
                continue;
            }
            break;
        }
        return left;
    }
    int64 parse_mul() {
        int64 left = this->parse_unary();
        while (true) {
            if (this->match("STAR")) {
                int64 right = this->parse_unary();
                left = this->add_expr(::rc_new<ExprNode>("bin", 0, "", "*", left, right));
                continue;
            }
            if (this->match("SLASH")) {
                int64 right = this->parse_unary();
                left = this->add_expr(::rc_new<ExprNode>("bin", 0, "", "/", left, right));
                continue;
            }
            break;
        }
        return left;
    }
    int64 parse_unary() {
        if (this->match("MINUS")) {
            int64 child = this->parse_unary();
            return this->add_expr(::rc_new<ExprNode>("neg", 0, "", "", child, -1));
        }
        return this->parse_primary();
    }
    int64 parse_primary() {
        if (this->match("NUMBER")) {
            rc<Token> token_num = obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos - 1)), "subscript:list");
            return this->add_expr(::rc_new<ExprNode>("lit", py_to_int64(token_num->text), "", "", -1, -1));
        }
        if (this->match("IDENT")) {
            rc<Token> token_ident = obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos - 1)), "subscript:list");
            return this->add_expr(::rc_new<ExprNode>("var", 0, token_ident->text, "", -1, -1));
        }
        if (this->match("LPAREN")) {
            int64 expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        rc<Token> t = obj_to_rc_or_raise<Token>(py_at(this->tokens, py_to<int64>(this->pos)), "subscript:list");
        throw ::std::runtime_error("primary parse error at pos=" + py_to_string(t->pos) + " got=" + t->kind);
    }
};

int64 eval_expr(int64 expr_index, const object& expr_nodes, const dict<str, int64>& env) {
    rc<ExprNode> node = obj_to_rc_or_raise<ExprNode>(py_at(expr_nodes, py_to<int64>(expr_index)), "subscript:list");
    
    if (node->kind == "lit")
        return node->value;
    if (node->kind == "var") {
        if (!(py_contains(env, node->name)))
            throw ::std::runtime_error("undefined variable: " + node->name);
        return py_dict_get(env, node->name);
    }
    if (node->kind == "neg")
        return -eval_expr(node->left, expr_nodes, env);
    if (node->kind == "bin") {
        int64 lhs = eval_expr(node->left, expr_nodes, env);
        int64 rhs = eval_expr(node->right, expr_nodes, env);
        if (node->op == "+")
            return lhs + rhs;
        if (node->op == "-")
            return lhs - rhs;
        if (node->op == "*")
            return lhs * rhs;
        if (node->op == "/") {
            if (rhs == 0)
                throw ::std::runtime_error("division by zero");
            return lhs / rhs;
        }
        throw ::std::runtime_error("unknown operator: " + node->op);
    }
    throw ::std::runtime_error("unknown node kind: " + node->kind);
}

int64 execute(const object& stmts, const object& expr_nodes, bool trace) {
    dict<str, int64> env = dict<str, int64>{};
    int64 checksum = 0;
    int64 printed = 0;
    
    for (rc<StmtNode> stmt : py_to_rc_list_from_object<StmtNode>(stmts, "for_target:stmt")) {
        if (stmt->kind == "let") {
            env[stmt->name] = eval_expr(stmt->expr_index, expr_nodes, env);
            continue;
        }
        if (stmt->kind == "assign") {
            if (!(py_contains(env, stmt->name)))
                throw ::std::runtime_error("assign to undefined variable: " + stmt->name);
            env[stmt->name] = eval_expr(stmt->expr_index, expr_nodes, env);
            continue;
        }
        int64 value = eval_expr(stmt->expr_index, expr_nodes, env);
        if (trace)
            py_print(value);
        int64 norm = value % 1000000007;
        if (norm < 0)
            norm += 1000000007;
        checksum = (checksum * 131 + norm) % 1000000007;
        printed++;
    }
    if (trace)
        py_print("printed:", printed);
    return checksum;
}

object build_benchmark_source(int64 var_count, int64 loops) {
    object lines = make_object(list<object>{});
    
    // Declare initial variables.
    for (int64 i = 0; i < var_count; ++i) {
        py_append(lines, make_object("let v" + ::std::to_string(i) + " = " + ::std::to_string(i + 1)));
    }
    // Force evaluation of many arithmetic expressions.
    for (int64 i = 0; i < loops; ++i) {
        int64 x = i % var_count;
        int64 y = (i + 3) % var_count;
        int64 c1 = i % 7 + 1;
        int64 c2 = i % 11 + 2;
        py_append(lines, make_object("v" + ::std::to_string(x) + " = (v" + ::std::to_string(x) + " * " + ::std::to_string(c1) + " + v" + ::std::to_string(y) + " + 10000) / " + ::std::to_string(c2)));
        if (i % 97 == 0)
            py_append(lines, make_object("print v" + ::std::to_string(x)));
    }
    // Print final values together.
    py_append(lines, make_object("print (v0 + v1 + v2 + v3)"));
    return lines;
}

void run_demo() {
    object demo_lines = make_object(list<object>{});
    py_append(demo_lines, make_object("let a = 10"));
    py_append(demo_lines, make_object("let b = 3"));
    py_append(demo_lines, make_object("a = (a + b) * 2"));
    py_append(demo_lines, make_object("print a"));
    py_append(demo_lines, make_object("print a / b"));
    
    object tokens = tokenize(demo_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    object stmts = parser->parse_program();
    int64 checksum = execute(stmts, make_object(parser->expr_nodes), true);
    py_print("demo_checksum:", checksum);
}

void run_benchmark() {
    object source_lines = build_benchmark_source(32, 120000);
    float64 start = pytra::std::time::perf_counter();
    object tokens = tokenize(source_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    object stmts = parser->parse_program();
    int64 checksum = execute(stmts, make_object(parser->expr_nodes), false);
    float64 elapsed = pytra::std::time::perf_counter() - start;
    
    py_print("token_count:", py_len(tokens));
    py_print("expr_count:", py_len(parser->expr_nodes));
    py_print("stmt_count:", py_len(stmts));
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

void __pytra_main() {
    run_demo();
    run_benchmark();
}

int main(int argc, char** argv) {
    pytra_configure_from_argv(argc, argv);
    __pytra_main();
    return 0;
}
