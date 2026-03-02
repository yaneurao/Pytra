#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/dataclasses.h"
#include "pytra/std/time.h"

struct Token {
    str kind;
    str text;
    int64 pos;
    int64 number_value;
    
    Token(str kind, str text, int64 pos, int64 number_value) : kind(kind), text(text), pos(pos), number_value(number_value) {
    }
    
};

struct ExprNode {
    str kind;
    int64 value;
    str name;
    str op;
    int64 left;
    int64 right;
    int64 kind_tag;
    int64 op_tag;
    
    ExprNode(str kind, int64 value, str name, str op, int64 left, int64 right, int64 kind_tag, int64 op_tag) : kind(kind), value(value), name(name), op(op), left(left), right(right), kind_tag(kind_tag), op_tag(op_tag) {
    }
    
};

struct StmtNode {
    str kind;
    str name;
    int64 expr_index;
    int64 kind_tag;
    
    StmtNode(str kind, str name, int64 expr_index, int64 kind_tag) : kind(kind), name(name), expr_index(expr_index), kind_tag(kind_tag) {
    }
    
};

list<Token> tokenize(const list<str>& lines) {
    dict<str, int64> single_char_token_tags = dict<str, int64>{{"+", 1}, {"-", 2}, {"*", 3}, {"/", 4}, {"(", 5}, {")", 6}, {"=", 7}};
    list<str> single_char_token_kinds = list<str>{"PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"};
    list<Token> tokens = {};
    for (const auto& [line_index, source] : py_enumerate(lines)) {
        int64 i = 0;
        int64 n = py_len(source);
        while (i < n) {
            str ch = source[i];
            
            if (ch == " ") {
                i++;
                continue;
            }
            int64 single_tag = py_to<int64>(single_char_token_tags.get(ch, 0));
            if (single_tag > 0) {
                tokens.append(Token(Token(single_char_token_kinds[single_tag - 1], ch, i, 0)));
                i++;
                continue;
            }
            if (ch.isdigit()) {
                int64 start = i;
                while ((i < n) && (source[i].isdigit())) {
                    i++;
                }
                str text = py_slice(source, start, i);
                tokens.append(Token(Token("NUMBER", text, start, py_to_int64(text))));
                continue;
            }
            if ((ch.isalpha()) || (ch == "_")) {
                int64 start = i;
                while ((i < n) && (((source[i].isalpha()) || (source[i] == "_")) || (source[i].isdigit()))) {
                    i++;
                }
                str text = py_slice(source, start, i);
                if (text == "let") {
                    tokens.append(Token(Token("LET", text, start, 0)));
                } else if (text == "print") {
                    tokens.append(Token(Token("PRINT", text, start, 0)));
                } else {
                    tokens.append(Token(Token("IDENT", text, start, 0)));
                }
                continue;
            }
            throw ::std::runtime_error("tokenize error at line=" + ::std::to_string(line_index) + " pos=" + ::std::to_string(i) + " ch=" + ch);
        }
        tokens.append(Token(Token("NEWLINE", "", n, 0)));
    }
    tokens.append(Token(Token("EOF", "", py_len(lines), 0)));
    return tokens;
}

struct Parser : public PyObj {
    list<ExprNode> expr_nodes;
    int64 pos;
    list<Token> tokens;
    PYTRA_DECLARE_CLASS_TYPE(PYTRA_TID_OBJECT);
    
    list<ExprNode> new_expr_nodes() {
        return list<ExprNode>{};
    }
    Parser(const list<Token>& tokens) {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    Token current_token() {
        return this->tokens[this->pos];
    }
    Token previous_token() {
        return this->tokens[this->pos - 1];
    }
    str peek_kind() {
        return this->current_token().kind;
    }
    bool match(const str& kind) {
        if (this->peek_kind() == kind) {
            this->pos++;
            return true;
        }
        return false;
    }
    Token expect(const str& kind) {
        Token token = this->current_token();
        if (token.kind != kind)
            throw ::std::runtime_error("parse error at pos=" + py_to_string(token.pos) + ", expected=" + kind + ", got=" + token.kind);
        this->pos++;
        return token;
    }
    void skip_newlines() {
        while (this->match("NEWLINE")) {
            ;
        }
    }
    int64 add_expr(const ExprNode& node) {
        this->expr_nodes.append(node);
        return py_len(this->expr_nodes) - 1;
    }
    list<StmtNode> parse_program() {
        list<StmtNode> stmts = {};
        this->skip_newlines();
        while (this->peek_kind() != "EOF") {
            StmtNode stmt = this->parse_stmt();
            stmts.append(stmt);
            this->skip_newlines();
        }
        return stmts;
    }
    StmtNode parse_stmt() {
        if (this->match("LET")) {
            str let_name = this->expect("IDENT").text;
            this->expect("EQUAL");
            int64 let_expr_index = this->parse_expr();
            return StmtNode("let", let_name, let_expr_index, 1);
        }
        if (this->match("PRINT")) {
            int64 print_expr_index = this->parse_expr();
            return StmtNode("print", "", print_expr_index, 3);
        }
        str assign_name = this->expect("IDENT").text;
        this->expect("EQUAL");
        int64 assign_expr_index = this->parse_expr();
        return StmtNode("assign", assign_name, assign_expr_index, 2);
    }
    int64 parse_expr() {
        return this->parse_add();
    }
    int64 parse_add() {
        int64 left = this->parse_mul();
        while (true) {
            if (this->match("PLUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "+", left, right, 3, 1));
                continue;
            }
            if (this->match("MINUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "-", left, right, 3, 2));
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
                left = this->add_expr(ExprNode("bin", 0, "", "*", left, right, 3, 3));
                continue;
            }
            if (this->match("SLASH")) {
                int64 right = this->parse_unary();
                left = this->add_expr(ExprNode("bin", 0, "", "/", left, right, 3, 4));
                continue;
            }
            break;
        }
        return left;
    }
    int64 parse_unary() {
        if (this->match("MINUS")) {
            int64 child = this->parse_unary();
            return this->add_expr(ExprNode("neg", 0, "", "", child, -1, 4, 0));
        }
        return this->parse_primary();
    }
    int64 parse_primary() {
        if (this->match("NUMBER")) {
            Token token_num = this->previous_token();
            return this->add_expr(ExprNode("lit", token_num.number_value, "", "", -1, -1, 1, 0));
        }
        if (this->match("IDENT")) {
            Token token_ident = this->previous_token();
            return this->add_expr(ExprNode("var", 0, token_ident.text, "", -1, -1, 2, 0));
        }
        if (this->match("LPAREN")) {
            int64 expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        Token t = this->current_token();
        throw ::std::runtime_error("primary parse error at pos=" + py_to_string(t.pos) + " got=" + t.kind);
    }
};

int64 eval_expr(int64 expr_index, const list<ExprNode>& expr_nodes, const dict<str, int64>& env) {
    ExprNode node = expr_nodes[expr_index];
    
    if (node.kind_tag == 1)
        return node.value;
    if (node.kind_tag == 2) {
        if (!(py_contains(env, node.name)))
            throw ::std::runtime_error("undefined variable: " + node.name);
        return py_dict_get(env, node.name);
    }
    if (node.kind_tag == 4)
        return -eval_expr(node.left, expr_nodes, env);
    if (node.kind_tag == 3) {
        int64 lhs = eval_expr(node.left, expr_nodes, env);
        int64 rhs = eval_expr(node.right, expr_nodes, env);
        if (node.op_tag == 1)
            return lhs + rhs;
        if (node.op_tag == 2)
            return lhs - rhs;
        if (node.op_tag == 3)
            return lhs * rhs;
        if (node.op_tag == 4) {
            if (rhs == 0)
                throw ::std::runtime_error("division by zero");
            return lhs / rhs;
        }
        throw ::std::runtime_error("unknown operator: " + node.op);
    }
    throw ::std::runtime_error("unknown node kind: " + node.kind);
}

int64 execute(const list<StmtNode>& stmts, const list<ExprNode>& expr_nodes, bool trace) {
    dict<str, int64> env = {};
    int64 checksum = 0;
    int64 printed = 0;
    
    for (StmtNode stmt : stmts) {
        if (stmt.kind_tag == 1) {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        if (stmt.kind_tag == 2) {
            if (!(py_contains(env, stmt.name)))
                throw ::std::runtime_error("assign to undefined variable: " + stmt.name);
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        int64 value = eval_expr(stmt.expr_index, expr_nodes, env);
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
    list<str> lines = {};
    
    // Declare initial variables.
    lines.reserve((var_count <= 0) ? 0 : var_count);
    for (int64 i = 0; i < var_count; ++i)
        lines.append(str("let v" + ::std::to_string(i) + " = " + ::std::to_string(i + 1)));
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
    list<str> demo_lines = {};
    demo_lines.append(str("let a = 10"));
    demo_lines.append(str("let b = 3"));
    demo_lines.append(str("a = (a + b) * 2"));
    demo_lines.append(str("print a"));
    demo_lines.append(str("print a / b"));
    
    list<Token> tokens = tokenize(demo_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    list<StmtNode> stmts = parser->parse_program();
    int64 checksum = execute(stmts, parser->expr_nodes, true);
    py_print("demo_checksum:", checksum);
}

void run_benchmark() {
    list<str> source_lines = build_benchmark_source(32, 120000);
    float64 start = pytra::std::time::perf_counter();
    list<Token> tokens = tokenize(source_lines);
    rc<Parser> parser = ::rc_new<Parser>(tokens);
    list<StmtNode> stmts = parser->parse_program();
    int64 checksum = execute(stmts, parser->expr_nodes, false);
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
