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

list<rc<Token>> tokenize(const list<str>& lines) {
    list<rc<Token>> tokens = list<rc<Token>>{};
    for (object __itobj_1 : py_dyn_range(py_enumerate(lines))) {
        auto line_index = py_at(__itobj_1, 0);
        auto source = py_at(__itobj_1, 1);
        int64 i = 0;
        int64 n = py_len(source);
        while (i < n) {
            str ch = py_at(source, py_to<int64>(i));
            
            if (ch == " ") {
                i++;
                continue;
            }
            if (ch == "+") {
                tokens.append(rc<Token>(::rc_new<Token>("PLUS", ch, i)));
                i++;
                continue;
            }
            if (ch == "-") {
                tokens.append(rc<Token>(::rc_new<Token>("MINUS", ch, i)));
                i++;
                continue;
            }
            if (ch == "*") {
                tokens.append(rc<Token>(::rc_new<Token>("STAR", ch, i)));
                i++;
                continue;
            }
            if (ch == "/") {
                tokens.append(rc<Token>(::rc_new<Token>("SLASH", ch, i)));
                i++;
                continue;
            }
            if (ch == "(") {
                tokens.append(rc<Token>(::rc_new<Token>("LPAREN", ch, i)));
                i++;
                continue;
            }
            if (ch == ")") {
                tokens.append(rc<Token>(::rc_new<Token>("RPAREN", ch, i)));
                i++;
                continue;
            }
            if (ch == "=") {
                tokens.append(rc<Token>(::rc_new<Token>("EQUAL", ch, i)));
                i++;
                continue;
            }
            if (str(ch).isdigit()) {
                int64 start = i;
                while ((i < n) && (str(py_at(source, py_to<int64>(i))).isdigit())) {
                    i++;
                }
                str text = py_slice(source, start, i);
                tokens.append(rc<Token>(::rc_new<Token>("NUMBER", text, start)));
                continue;
            }
            if ((str(ch).isalpha()) || (ch == "_")) {
                int64 start = i;
                while ((i < n) && (((str(py_at(source, py_to<int64>(i))).isalpha()) || (py_at(source, py_to<int64>(i)) == "_")) || (str(py_at(source, py_to<int64>(i))).isdigit()))) {
                    i++;
                }
                str text = py_slice(source, start, i);
                if (text == "let") {
                    tokens.append(rc<Token>(::rc_new<Token>("LET", text, start)));
                } else {
                    if (text == "print")
                        tokens.append(rc<Token>(::rc_new<Token>("PRINT", text, start)));
                    else
                        tokens.append(rc<Token>(::rc_new<Token>("IDENT", text, start)));
                }
                continue;
            }
            throw ::std::runtime_error("tokenize error at line=" + py_to_string(line_index) + " pos=" + ::std::to_string(i) + " ch=" + ch);
        }
        tokens.append(rc<Token>(::rc_new<Token>("NEWLINE", "", n)));
    }
    tokens.append(rc<Token>(::rc_new<Token>("EOF", "", py_len(lines))));
    return tokens;
}

struct Parser : public PyObj {
    list<rc<ExprNode>> expr_nodes;
    int64 pos;
    list<rc<Token>> tokens;
    inline static uint32 PYTRA_TYPE_ID = py_register_class_type(PYTRA_TID_OBJECT);
    uint32 py_type_id() const noexcept override {
        return PYTRA_TYPE_ID;
    }
    virtual bool py_isinstance_of(uint32 expected_type_id) const override {
        return expected_type_id == PYTRA_TYPE_ID;
    }
    
    list<rc<ExprNode>> new_expr_nodes() {
        return list<object>{};
    }
    Parser(const list<rc<Token>>& tokens) {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    str peek_kind() {
        return this->tokens[this->pos]->kind;
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
            rc<Token> t = this->tokens[this->pos];
            throw ::std::runtime_error("parse error at pos=" + py_to_string(t->pos) + ", expected=" + kind + ", got=" + t->kind);
        }
        rc<Token> token = this->tokens[this->pos];
        this->pos++;
        return token;
    }
    void skip_newlines() {
        while (this->match("NEWLINE")) {
            /* pass */
        }
    }
    int64 add_expr(const rc<ExprNode>& node) {
        this->expr_nodes.append(rc<ExprNode>(node));
        return py_len(this->expr_nodes) - 1;
    }
    list<rc<StmtNode>> parse_program() {
        list<rc<StmtNode>> stmts = list<rc<StmtNode>>{};
        this->skip_newlines();
        while (this->peek_kind() != "EOF") {
            rc<StmtNode> stmt = this->parse_stmt();
            stmts.append(rc<StmtNode>(stmt));
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
            rc<Token> token_num = this->tokens[this->pos - 1];
            return this->add_expr(::rc_new<ExprNode>("lit", py_to_int64(token_num->text), "", "", -1, -1));
        }
        if (this->match("IDENT")) {
            rc<Token> token_ident = this->tokens[this->pos - 1];
            return this->add_expr(::rc_new<ExprNode>("var", 0, token_ident->text, "", -1, -1));
        }
        if (this->match("LPAREN")) {
            int64 expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        rc<Token> t = this->tokens[this->pos];
        throw ::std::runtime_error("primary parse error at pos=" + py_to_string(t->pos) + " got=" + t->kind);
    }
};

int64 eval_expr(int64 expr_index, const list<rc<ExprNode>>& expr_nodes, const dict<str, int64>& env) {
    rc<ExprNode> node = expr_nodes[expr_index];
    
    if (node->kind == "lit")
        return node->value;
    if (node->kind == "var") {
        if (!(py_contains(env, node->name)))
            throw ::std::runtime_error("undefined variable: " + node->name);
        return py_dict_get(env, py_to_string(node->name));
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

int64 execute(const list<rc<StmtNode>>& stmts, const list<rc<ExprNode>>& expr_nodes, bool trace) {
    dict<str, int64> env = dict<str, int64>{};
    int64 checksum = 0;
    int64 printed = 0;
    
    for (object __itobj_2 : py_dyn_range(stmts)) {
        rc<StmtNode> stmt = obj_to_rc_or_raise<StmtNode>(__itobj_2, "for_target:stmt");
        if (stmt->kind == "let") {
            env[py_to_string(stmt->name)] = eval_expr(stmt->expr_index, expr_nodes, env);
            continue;
        }
        if (stmt->kind == "assign") {
            if (!(py_contains(env, stmt->name)))
                throw ::std::runtime_error("assign to undefined variable: " + stmt->name);
            env[py_to_string(stmt->name)] = eval_expr(stmt->expr_index, expr_nodes, env);
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

list<str> build_benchmark_source(int64 var_count, int64 loops) {
    list<str> lines = list<str>{};
    
    // Declare initial variables.
    for (int64 i = 0; i < var_count; ++i) {
        lines.append(str("let v" + ::std::to_string(i) + " = " + ::std::to_string(i + 1)));
    }
    // Force evaluation of many arithmetic expressions.
    for (int64 i = 0; i < loops; ++i) {
        int64 x = i % var_count;
        int64 y = (i + 3) % var_count;
        int64 c1 = i % 7 + 1;
        int64 c2 = i % 11 + 2;
        lines.append(str("v" + ::std::to_string(x) + " = (v" + ::std::to_string(x) + " * " + ::std::to_string(c1) + " + v" + ::std::to_string(y) + " + 10000) / " + ::std::to_string(c2)));
        if (i % 97 == 0)
            lines.append(str("print v" + ::std::to_string(x)));
    }
    // Print final values together.
    lines.append(str("print (v0 + v1 + v2 + v3)"));
    return lines;
}

void run_demo() {
    list<str> demo_lines = list<str>{};
    demo_lines.append(str("let a = 10"));
    demo_lines.append(str("let b = 3"));
    demo_lines.append(str("a = (a + b) * 2"));
    demo_lines.append(str("print a"));
    demo_lines.append(str("print a / b"));
    
    list<rc<Token>> tokens = tokenize(demo_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    list<rc<StmtNode>> stmts = parser->parse_program();
    int64 checksum = execute(stmts, parser->expr_nodes, true);
    py_print("demo_checksum:", checksum);
}

void run_benchmark() {
    list<str> source_lines = build_benchmark_source(32, 120000);
    float64 start = py_to<float64>(pytra::std::time::perf_counter());
    list<rc<Token>> tokens = tokenize(source_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    list<rc<StmtNode>> stmts = parser->parse_program();
    int64 checksum = execute(stmts, parser->expr_nodes, false);
    float64 elapsed = py_to<float64>(pytra::std::time::perf_counter() - start);
    
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
