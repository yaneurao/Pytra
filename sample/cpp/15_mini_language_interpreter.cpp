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

list<Token> tokenize(list<str> lines) {
    str source;
    int64 i;
    int64 n;
    str ch;
    int64 start;
    str text;
    
    list<Token> tokens = list<Token>{};
    int64 line_index = 0;
    while (line_index < py_len(lines)) {
        source = lines[line_index];
        i = 0;
        n = py_len(source);
        while (i < n) {
            ch = py_slice(source, i, i + 1);
            
            if (ch == " ") {
                i++;
                continue;
            }
            
            if (ch == "+") {
                tokens.push_back(Token("PLUS", ch, i));
                i++;
                continue;
            }
            
            if (ch == "-") {
                tokens.push_back(Token("MINUS", ch, i));
                i++;
                continue;
            }
            
            if (ch == "*") {
                tokens.push_back(Token("STAR", ch, i));
                i++;
                continue;
            }
            
            if (ch == "/") {
                tokens.push_back(Token("SLASH", ch, i));
                i++;
                continue;
            }
            
            if (ch == "(") {
                tokens.push_back(Token("LPAREN", ch, i));
                i++;
                continue;
            }
            
            if (ch == ")") {
                tokens.push_back(Token("RPAREN", ch, i));
                i++;
                continue;
            }
            
            if (ch == "=") {
                tokens.push_back(Token("EQUAL", ch, i));
                i++;
                continue;
            }
            
            if (py_isdigit(ch)) {
                start = i;
                while ((i < n) && (py_isdigit(py_slice(source, i, i + 1)))) {
                    i++;
                }
                text = py_slice(source, start, i);
                tokens.push_back(Token("NUMBER", text, start));
                continue;
            }
            
            if ((py_isalpha(ch)) || (ch == "_")) {
                start = i;
                while ((i < n) && (((py_isalpha(py_slice(source, i, i + 1))) || (py_slice(source, i, i + 1) == "_")) || (py_isdigit(py_slice(source, i, i + 1))))) {
                    i++;
                }
                text = py_slice(source, start, i);
                if (text == "let") {
                    tokens.push_back(Token("LET", text, start));
                } else {
                    if (text == "print")
                        tokens.push_back(Token("PRINT", text, start));
                    else
                        tokens.push_back(Token("IDENT", text, start));
                }
                continue;
            }
            
            throw std::runtime_error("tokenize error at line=" + std::to_string(line_index) + " pos=" + std::to_string(i) + " ch=" + ch);
        }
        
        tokens.push_back(Token("NEWLINE", "", n));
        line_index++;
    }
    
    tokens.push_back(Token("EOF", "", py_len(lines)));
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
    Parser(list<Token> tokens) {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    str peek_kind() {
        return this->tokens[this->pos].kind;
    }
    bool match(str kind) {
        if (this->peek_kind() == kind) {
            this->pos++;
            return true;
        }
        return false;
    }
    Token expect(str kind) {
        
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
    int64 add_expr(ExprNode node) {
        this->expr_nodes.push_back(node);
        return py_len(this->expr_nodes) - 1;
    }
    list<StmtNode> parse_program() {
        
        list<StmtNode> stmts = list<StmtNode>{};
        this->skip_newlines();
        while (this->peek_kind() != "EOF") {
            StmtNode stmt = this->parse_stmt();
            stmts.push_back(stmt);
            this->skip_newlines();
        }
        return stmts;
    }
    StmtNode parse_stmt() {
        str let_name;
        int64 let_expr_index;
        int64 print_expr_index;
        
        if (this->match("LET")) {
            let_name = this->expect("IDENT").text;
            this->expect("EQUAL");
            let_expr_index = this->parse_expr();
            return StmtNode("let", let_name, let_expr_index);
        }
        
        if (this->match("PRINT")) {
            print_expr_index = this->parse_expr();
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
        int64 right;
        
        int64 left = this->parse_mul();
        bool done = false;
        while (!(done)) {
            if (this->match("PLUS")) {
                right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "+", left, right));
                continue;
            }
            if (this->match("MINUS")) {
                right = this->parse_mul();
                left = this->add_expr(ExprNode("bin", 0, "", "-", left, right));
                continue;
            }
            done = true;
        }
        return left;
    }
    int64 parse_mul() {
        int64 right;
        
        int64 left = this->parse_unary();
        bool done = false;
        while (!(done)) {
            if (this->match("STAR")) {
                right = this->parse_unary();
                left = this->add_expr(ExprNode("bin", 0, "", "*", left, right));
                continue;
            }
            if (this->match("SLASH")) {
                right = this->parse_unary();
                left = this->add_expr(ExprNode("bin", 0, "", "/", left, right));
                continue;
            }
            done = true;
        }
        return left;
    }
    int64 parse_unary() {
        int64 child;
        
        if (this->match("MINUS")) {
            child = this->parse_unary();
            return this->add_expr(ExprNode("neg", 0, "", "", child, -1));
        }
        return this->parse_primary();
    }
    int64 parse_primary() {
        int64 expr_index;
        
        if (this->match("NUMBER")) {
            Token token_num = this->tokens[this->pos - 1];
            return this->add_expr(ExprNode("lit", py_to_int64(token_num.text), "", "", -1, -1));
        }
        
        if (this->match("IDENT")) {
            Token token_ident = this->tokens[this->pos - 1];
            return this->add_expr(ExprNode("var", 0, token_ident.text, "", -1, -1));
        }
        
        if (this->match("LPAREN")) {
            expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        
        Token t = this->tokens[this->pos];
        throw std::runtime_error("primary parse error at pos=" + py_to_string(t.pos) + " got=" + t.kind);
    }
};

int64 eval_expr(int64 expr_index, list<ExprNode>& expr_nodes, dict<str, int64>& env) {
    int64 lhs;
    int64 rhs;
    
    ExprNode node = expr_nodes[expr_index];
    
    if (node.kind == "lit")
        return node.value;
    
    if (node.kind == "var") {
        if (env.find(node.name) == env.end())
            throw std::runtime_error("undefined variable: " + node.name);
        return env[node.name];
    }
    
    if (node.kind == "neg")
        return -eval_expr(node.left, expr_nodes, env);
    
    if (node.kind == "bin") {
        lhs = eval_expr(node.left, expr_nodes, env);
        rhs = eval_expr(node.right, expr_nodes, env);
        if (node.op == "+")
            return lhs + rhs;
        if (node.op == "-")
            return lhs - rhs;
        if (node.op == "*")
            return lhs * rhs;
        if (node.op == "/") {
            if (rhs == 0)
                throw std::runtime_error("division by zero");
            
            return py_floordiv(lhs, rhs);
        }
        throw std::runtime_error("unknown operator: " + node.op);
    }
    
    throw std::runtime_error("unknown node kind: " + node.kind);
}

int64 execute(list<StmtNode> stmts, list<ExprNode> expr_nodes, bool trace) {
    int64 value;
    int64 norm;
    
    dict<str, int64> env = dict<str, int64>{};
    int64 checksum = 0;
    int64 printed = 0;
    
    for (StmtNode stmt : stmts) {
        if (stmt.kind == "let") {
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        
        if (stmt.kind == "assign") {
            if (env.find(stmt.name) == env.end())
                throw std::runtime_error("assign to undefined variable: " + stmt.name);
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
            continue;
        }
        
        value = eval_expr(stmt.expr_index, expr_nodes, env);
        if (trace)
            py_print(value);
        norm = value % 1000000007;
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
    int64 x;
    int64 y;
    int64 c1;
    int64 c2;
    int64 i;
    
    list<str> lines = list<str>{};
    
    
    for (i = 0; i < var_count; ++i)
        lines.push_back("let v" + std::to_string(i) + " = " + std::to_string(i + 1));
    
    
    for (i = 0; i < loops; ++i) {
        x = i % var_count;
        y = (i + 3) % var_count;
        c1 = i % 7 + 1;
        c2 = i % 11 + 2;
        lines.push_back("v" + std::to_string(x) + " = (v" + std::to_string(x) + " * " + std::to_string(c1) + " + v" + std::to_string(y) + " + 10000) / " + std::to_string(c2));
        if (i % 97 == 0)
            lines.push_back("print v" + std::to_string(x));
    }
    
    
    lines.push_back("print (v0 + v1 + v2 + v3)");
    return lines;
}

void run_demo() {
    list<str> demo_lines = list<str>{};
    demo_lines.push_back("let a = 10");
    demo_lines.push_back("let b = 3");
    demo_lines.push_back("a = (a + b) * 2");
    demo_lines.push_back("print a");
    demo_lines.push_back("print a / b");
    
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

int main() {
    __pytra_main();
    return 0;
}
