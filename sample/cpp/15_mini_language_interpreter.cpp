#include "cpp_module/py_runtime.h"

struct Token {
    str kind;
    str text;
    int64 pos;
    
    Token(str kind, str text, int64 pos) {
        this->kind = kind;
        this->text = text;
        this->pos = pos;
    }
    
};

struct ExprNode {
    str kind;
    int64 value;
    str name;
    str op;
    int64 left;
    int64 right;
    
    ExprNode(str kind, int64 value, str name, str op, int64 left, int64 right) {
        this->kind = kind;
        this->value = value;
        this->name = name;
        this->op = op;
        this->left = left;
        this->right = right;
    }
    
};

struct StmtNode {
    str kind;
    str name;
    int64 expr_index;
    
    StmtNode(str kind, str name, int64 expr_index) {
        this->kind = kind;
        this->name = name;
        this->expr_index = expr_index;
    }
    
};

list<Token> tokenize(const list<str>& lines) {
    list<Token> tokens = list<Token>{};
    int64 line_index = 0;
    while (line_index < py_len(lines)) {
        str source = lines[line_index];
        int64 i = 0;
        int64 n = py_len(source);
        while (i < n) {
            str ch = py_slice(source, i, i + 1);
            
            if (ch == " ") {
                i++;
                continue;
            }
            
            if (ch == "+") {
                tokens.append(Token("PLUS", ch, i));
                i++;
                continue;
            }
            
            if (ch == "-") {
                tokens.append(Token("MINUS", ch, i));
                i++;
                continue;
            }
            
            if (ch == "*") {
                tokens.append(Token("STAR", ch, i));
                i++;
                continue;
            }
            
            if (ch == "/") {
                tokens.append(Token("SLASH", ch, i));
                i++;
                continue;
            }
            
            if (ch == "(") {
                tokens.append(Token("LPAREN", ch, i));
                i++;
                continue;
            }
            
            if (ch == ")") {
                tokens.append(Token("RPAREN", ch, i));
                i++;
                continue;
            }
            
            if (ch == "=") {
                tokens.append(Token("EQUAL", ch, i));
                i++;
                continue;
            }
            
            if (py_isdigit(ch)) {
                int64 start = i;
                while ((i < n) && (py_isdigit(py_slice(source, i, i + 1)))) {
                    i++;
                }
                str text = py_slice(source, start, i);
                tokens.append(Token("NUMBER", text, start));
                continue;
            }
            
            if ((py_isalpha(ch)) || (ch == "_")) {
                int64 start = i;
                while ((i < n) && (((py_isalpha(py_slice(source, i, i + 1))) || (py_slice(source, i, i + 1) == "_")) || (py_isdigit(py_slice(source, i, i + 1))))) {
                    i++;
                }
                str text = py_slice(source, start, i);
                if (text == "let") {
                    tokens.append(Token("LET", text, start));
                } else {
                    if (text == "print")
                        tokens.append(Token("PRINT", text, start));
                    else
                        tokens.append(Token("IDENT", text, start));
                }
                continue;
            }
            
            throw std::runtime_error("tokenize error at line=" + std::to_string(line_index) + " pos=" + std::to_string(i) + " ch=" + ch);
        }
        
        tokens.append(Token("NEWLINE", "", n));
        line_index++;
    }
    
    tokens.append(Token("EOF", "", py_len(lines)));
    return tokens;
}

struct Parser {
    list<Token> tokens;
    int64 pos;
    list<ExprNode> expr_nodes;
    
    list<ExprNode> new_expr_nodes() {
        list<ExprNode> nodes = list<ExprNode>{};
        return nodes;
    }
    Parser(const list<Token>& tokens) {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    str peek_kind() {
        return this->tokens[this->pos].kind;
    }
    bool match(const str& kind) {
        if (this->peek_kind() == kind) {
            this->pos++;
            return true;
        }
        return false;
    }
    Token expect(const str& kind) {
        if (this->peek_kind() != kind) {
            Token t = this->tokens[this->pos];
            throw std::runtime_error("parse error at pos=" + py_to_string(t.pos) + ", expected=" + kind + ", got=" + t.kind);
        }
        Token token = this->tokens[this->pos];
        
        this->pos++;
        return token;
    }
    void skip_newlines() {
        while (this->match("NEWLINE")) {
            /* pass */
        }
    }
    int64 add_expr(const ExprNode& node) {
        this->expr_nodes.append(node);
        return py_len(this->expr_nodes) - 1;
    }
    list<StmtNode> parse_program() {
        list<StmtNode> stmts = list<StmtNode>{};
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
            return StmtNode("let", let_name, let_expr_index);
        }
        
        if (this->match("PRINT")) {
            int64 print_expr_index = this->parse_expr();
            return StmtNode("print", "", print_expr_index);
        }
        
        str assign_name = this->expect("IDENT").text;
        this->expect("EQUAL");
        int64 assign_expr_index = this->parse_expr();
        return StmtNode("assign", assign_name, assign_expr_index);
    }
    int64 parse_expr() {
        return this->parse_add();
    }
    int64 parse_add() {
        int64 left = this->parse_mul();
        bool done = false;
        while (!(done)) {
            if (this->match("PLUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "+", left, right));
                continue;
            }
            if (this->match("MINUS")) {
                int64 right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "-", left, right));
                continue;
            }
            done = true;
        }
        return left;
    }
    int64 parse_mul() {
        int64 left = this->parse_unary();
        bool done = false;
        while (!(done)) {
            if (this->match("STAR")) {
                int64 right = this->parse_unary();
                left = this->add_expr(ExprNode("bin", 0, "", "*", left, right));
                continue;
            }
            if (this->match("SLASH")) {
                int64 right = this->parse_unary();
                left = this->add_expr(ExprNode("bin", 0, "", "/", left, right));
                continue;
            }
            done = true;
        }
        return left;
    }
    int64 parse_unary() {
        if (this->match("MINUS")) {
            int64 child = this->parse_unary();
            return this->add_expr(ExprNode("neg", 0, "", "", child, -1));
        }
        return this->parse_primary();
    }
    int64 parse_primary() {
        if (this->match("NUMBER")) {
            Token token_num = this->tokens[this->pos - 1];
            return this->add_expr(ExprNode("lit", py_to_int64(token_num.text), "", "", -1, -1));
        }
        
        if (this->match("IDENT")) {
            Token token_ident = this->tokens[this->pos - 1];
            return this->add_expr(ExprNode("var", 0, token_ident.text, "", -1, -1));
        }
        
        if (this->match("LPAREN")) {
            int64 expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        
        auto t = this->tokens[this->pos];
        throw std::runtime_error("primary parse error at pos=" + py_to_string(t.pos) + " got=" + t.kind);
    }
};

int64 eval_expr(int64 expr_index, const list<ExprNode>& expr_nodes, const dict<str, int64>& env) {
    ExprNode node = expr_nodes[expr_index];
    
    if (node.kind == "lit")
        return node.value;
    
    if (node.kind == "var") {
        if (!(env.find(node.name) != env.end()))
            throw std::runtime_error("undefined variable: " + node.name);
        return py_dict_get(env, node.name);
    }
    
    if (node.kind == "neg")
        return -eval_expr(node.left, expr_nodes, env);
    
    if (node.kind == "bin") {
        int64 lhs = eval_expr(node.left, expr_nodes, env);
        int64 rhs = eval_expr(node.right, expr_nodes, env);
        if (node.op == "+")
            return lhs + rhs;
        if (node.op == "-")
            return lhs - rhs;
        if (node.op == "*")
            return lhs * rhs;
        if (node.op == "/") {
            if (rhs == 0)
                throw std::runtime_error("division by zero");
            // ミニ言語では整数除算を採用する。
            return py_floordiv(lhs, rhs);
        }
        throw std::runtime_error("unknown operator: " + node.op);
    }
    
    throw std::runtime_error("unknown node kind: " + node.kind);
}

int64 execute(const list<StmtNode>& stmts, const list<ExprNode>& expr_nodes, bool trace) {
    dict<str, int64> env = dict<str, int64>{};
    int64 checksum = 0;
    int64 printed = 0;
    
    for (StmtNode stmt : stmts) {
        if (stmt.kind == "let") {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        
        if (stmt.kind == "assign") {
            if (!(env.find(stmt.name) != env.end()))
                throw std::runtime_error("assign to undefined variable: " + stmt.name);
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
    list<str> lines = list<str>{};
    
    // 初期変数を宣言。
    for (int64 i = 0; i < var_count; ++i)
        lines.append("let v" + std::to_string(i) + " = " + std::to_string(i + 1));
    
    // 算術式を大量に評価させる。
    for (int64 i = 0; i < loops; ++i) {
        int64 x = i % var_count;
        int64 y = (i + 3) % var_count;
        int64 c1 = i % 7 + 1;
        int64 c2 = i % 11 + 2;
        lines.append("v" + std::to_string(x) + " = (v" + std::to_string(x) + " * " + std::to_string(c1) + " + v" + std::to_string(y) + " + 10000) / " + std::to_string(c2));
        
        
        if (i % 97 == 0)
            lines.append("print v" + std::to_string(x));
    }
    
    // 最終値をまとめて出力。
    lines.append("print (v0 + v1 + v2 + v3)");
    return lines;
}

void run_demo() {
    list<str> demo_lines = list<str>{};
    demo_lines.append("let a = 10");
    demo_lines.append("let b = 3");
    demo_lines.append("a = (a + b) * 2");
    demo_lines.append("print a");
    demo_lines.append("print a / b");
    
    list<Token> tokens = tokenize(demo_lines);
    Parser parser = Parser(tokens);
    list<StmtNode> stmts = parser.parse_program();
    int64 checksum = execute(stmts, parser.expr_nodes, true);
    
    py_print("demo_checksum:", checksum);
}

void run_benchmark() {
    list<str> source_lines = build_benchmark_source(32, 120000);
    float64 start = perf_counter();
    list<Token> tokens = tokenize(source_lines);
    Parser parser = Parser(tokens);
    list<StmtNode> stmts = parser.parse_program();
    int64 checksum = execute(stmts, parser.expr_nodes, false);
    float64 elapsed = perf_counter() - start;
    
    py_print("token_count:", py_len(tokens));
    py_print("expr_count:", py_len(parser.expr_nodes));
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
