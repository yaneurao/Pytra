#include "cpp_module/dataclasses.h"
#include "cpp_module/gc.h"
#include "cpp_module/py_runtime.h"
#include "cpp_module/time.h"
#include <algorithm>
#include <any>
#include <cstdint>
#include <fstream>
#include <ios>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace std;
using namespace pycs::gc;

class Token : public pycs::gc::PyObj
{
public:
    string kind;
    string text;
    long long pos;
    Token(string kind, string text, long long pos)
    {
        this->kind = kind;
        this->text = text;
        this->pos = pos;
    }
};

class ExprNode : public pycs::gc::PyObj
{
public:
    string kind;
    long long value;
    string name;
    string op;
    long long left;
    long long right;
    ExprNode(string kind, long long value, string name, string op, long long left, long long right)
    {
        this->kind = kind;
        this->value = value;
        this->name = name;
        this->op = op;
        this->left = left;
        this->right = right;
    }
};

class StmtNode : public pycs::gc::PyObj
{
public:
    string kind;
    string name;
    long long expr_index;
    StmtNode(string kind, string name, long long expr_index)
    {
        this->kind = kind;
        this->name = name;
        this->expr_index = expr_index;
    }
};

class Parser : public pycs::gc::PyObj
{
public:
    vector<pycs::gc::RcHandle<Token>> tokens;
    long long pos;
    vector<pycs::gc::RcHandle<ExprNode>> expr_nodes;
    vector<pycs::gc::RcHandle<ExprNode>> new_expr_nodes()
    {
        vector<pycs::gc::RcHandle<ExprNode>> nodes = {};
        return nodes;
    }
    Parser(const vector<pycs::gc::RcHandle<Token>>& tokens)
    {
        this->tokens = tokens;
        this->pos = 0;
        this->expr_nodes = this->new_expr_nodes();
    }
    string peek_kind()
    {
        return py_get(this->tokens, this->pos)->kind;
    }
    bool match(const string& kind)
    {
        if ((this->peek_kind() == kind))
        {
            this->pos = (this->pos + 1);
            return true;
        }
        return false;
    }
    pycs::gc::RcHandle<Token> expect(const string& kind)
    {
        if ((this->peek_kind() != kind))
        {
            pycs::gc::RcHandle<Token> t = py_get(this->tokens, this->pos);
            throw std::runtime_error(py_to_string(((((("parse error at pos=" + py_to_string(t->pos)) + ", expected=") + kind) + ", got=") + t->kind)));
        }
        pycs::gc::RcHandle<Token> token = py_get(this->tokens, this->pos);
        this->pos = (this->pos + 1);
        return token;
    }
    void skip_newlines()
    {
        while (this->match("NEWLINE"))
        {
        }
    }
    long long add_expr(pycs::gc::RcHandle<ExprNode> node)
    {
        this->expr_nodes.push_back(node);
        return (py_len(this->expr_nodes) - 1);
    }
    vector<pycs::gc::RcHandle<StmtNode>> parse_program()
    {
        vector<pycs::gc::RcHandle<StmtNode>> stmts = {};
        this->skip_newlines();
        while ((this->peek_kind() != "EOF"))
        {
            pycs::gc::RcHandle<StmtNode> stmt = this->parse_stmt();
            stmts.push_back(stmt);
            this->skip_newlines();
        }
        return stmts;
    }
    pycs::gc::RcHandle<StmtNode> parse_stmt()
    {
        if (this->match("LET"))
        {
            string let_name = this->expect("IDENT")->text;
            this->expect("EQUAL");
            long long let_expr_index = this->parse_expr();
            return pycs::gc::RcHandle<StmtNode>::adopt(pycs::gc::rc_new<StmtNode>("let", let_name, let_expr_index));
        }
        if (this->match("PRINT"))
        {
            long long print_expr_index = this->parse_expr();
            return pycs::gc::RcHandle<StmtNode>::adopt(pycs::gc::rc_new<StmtNode>("print", "", print_expr_index));
        }
        string assign_name = this->expect("IDENT")->text;
        this->expect("EQUAL");
        long long assign_expr_index = this->parse_expr();
        return pycs::gc::RcHandle<StmtNode>::adopt(pycs::gc::rc_new<StmtNode>("assign", assign_name, assign_expr_index));
    }
    long long parse_expr()
    {
        return this->parse_add();
    }
    long long parse_add()
    {
        long long left = this->parse_mul();
        bool done = false;
        while ((!done))
        {
            if (this->match("PLUS"))
            {
                long long right = this->parse_mul();
                left = this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("bin", 0, "", "+", left, right)));
                continue;
            }
            if (this->match("MINUS"))
            {
                auto right = this->parse_mul();
                left = this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("bin", 0, "", "-", left, right)));
                continue;
            }
            done = true;
        }
        return left;
    }
    long long parse_mul()
    {
        long long left = this->parse_unary();
        bool done = false;
        while ((!done))
        {
            if (this->match("STAR"))
            {
                long long right = this->parse_unary();
                left = this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("bin", 0, "", "*", left, right)));
                continue;
            }
            if (this->match("SLASH"))
            {
                auto right = this->parse_unary();
                left = this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("bin", 0, "", "/", left, right)));
                continue;
            }
            done = true;
        }
        return left;
    }
    long long parse_unary()
    {
        if (this->match("MINUS"))
        {
            long long child = this->parse_unary();
            return this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("neg", 0, "", "", child, (-1))));
        }
        return this->parse_primary();
    }
    long long parse_primary()
    {
        if (this->match("NUMBER"))
        {
            pycs::gc::RcHandle<Token> token_num = py_get(this->tokens, (this->pos - 1));
            return this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("lit", py_int(token_num->text), "", "", (-1), (-1))));
        }
        if (this->match("IDENT"))
        {
            pycs::gc::RcHandle<Token> token_ident = py_get(this->tokens, (this->pos - 1));
            return this->add_expr(pycs::gc::RcHandle<ExprNode>::adopt(pycs::gc::rc_new<ExprNode>("var", 0, token_ident->text, "", (-1), (-1))));
        }
        if (this->match("LPAREN"))
        {
            long long expr_index = this->parse_expr();
            this->expect("RPAREN");
            return expr_index;
        }
        auto t = py_get(this->tokens, this->pos);
        throw std::runtime_error(py_to_string(((("primary parse error at pos=" + py_to_string(t->pos)) + " got=") + t->kind)));
    }
};

vector<pycs::gc::RcHandle<Token>> tokenize(const vector<string>& lines)
{
    vector<pycs::gc::RcHandle<Token>> tokens = {};
    long long line_index = 0;
    while ((line_index < py_len(lines)))
    {
        string source = py_get(lines, line_index);
        long long i = 0;
        long long n = py_len(source);
        while ((i < n))
        {
            string ch = py_slice(source, true, i, true, (i + 1));
            if ((ch == " "))
            {
                i = (i + 1);
                continue;
            }
            if ((ch == "+"))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("PLUS", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == "-"))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("MINUS", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == "*"))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("STAR", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == "/"))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("SLASH", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == "("))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("LPAREN", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == ")"))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("RPAREN", ch, i)));
                i = (i + 1);
                continue;
            }
            if ((ch == "="))
            {
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("EQUAL", ch, i)));
                i = (i + 1);
                continue;
            }
            if (py_isdigit(ch))
            {
                long long start = i;
                while (((i < n) && py_isdigit(py_slice(source, true, i, true, (i + 1)))))
                {
                    i = (i + 1);
                }
                string text = py_slice(source, true, start, true, i);
                tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("NUMBER", text, start)));
                continue;
            }
            if ((py_isalpha(ch) || (ch == "_")))
            {
                auto start = i;
                while (((i < n) && ((py_isalpha(py_slice(source, true, i, true, (i + 1))) || (py_slice(source, true, i, true, (i + 1)) == "_")) || py_isdigit(py_slice(source, true, i, true, (i + 1))))))
                {
                    i = (i + 1);
                }
                auto text = py_slice(source, true, start, true, i);
                if ((text == "let"))
                {
                    tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("LET", text, start)));
                }
                else
                {
                    if ((text == "print"))
                    {
                        tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("PRINT", text, start)));
                    }
                    else
                    {
                        tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("IDENT", text, start)));
                    }
                }
                continue;
            }
            throw std::runtime_error(py_to_string(((((("tokenize error at line=" + py_to_string(line_index)) + " pos=") + py_to_string(i)) + " ch=") + ch)));
        }
        tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("NEWLINE", "", n)));
        line_index = (line_index + 1);
    }
    tokens.push_back(pycs::gc::RcHandle<Token>::adopt(pycs::gc::rc_new<Token>("EOF", "", py_len(lines))));
    return tokens;
}

long long eval_expr(long long expr_index, const vector<pycs::gc::RcHandle<ExprNode>>& expr_nodes, const unordered_map<string, long long>& env)
{
    pycs::gc::RcHandle<ExprNode> node = py_get(expr_nodes, expr_index);
    if ((node->kind == "lit"))
    {
        return node->value;
    }
    if ((node->kind == "var"))
    {
        if ((!py_in(node->name, env)))
        {
            throw std::runtime_error(py_to_string(("undefined variable: " + node->name)));
        }
        return py_get(env, node->name);
    }
    if ((node->kind == "neg"))
    {
        return (-eval_expr(node->left, expr_nodes, env));
    }
    if ((node->kind == "bin"))
    {
        long long lhs = eval_expr(node->left, expr_nodes, env);
        long long rhs = eval_expr(node->right, expr_nodes, env);
        if ((node->op == "+"))
        {
            return (lhs + rhs);
        }
        if ((node->op == "-"))
        {
            return (lhs - rhs);
        }
        if ((node->op == "*"))
        {
            return (lhs * rhs);
        }
        if ((node->op == "/"))
        {
            if ((rhs == 0))
            {
                throw std::runtime_error(py_to_string("division by zero"));
            }
            return py_floordiv(lhs, rhs);
        }
        throw std::runtime_error(py_to_string(("unknown operator: " + node->op)));
    }
    throw std::runtime_error(py_to_string(("unknown node kind: " + node->kind)));
}

long long execute(const vector<pycs::gc::RcHandle<StmtNode>>& stmts, const vector<pycs::gc::RcHandle<ExprNode>>& expr_nodes, bool trace)
{
    unordered_map<string, long long> env = {};
    long long checksum = 0;
    long long printed = 0;
    for (const auto& stmt : stmts)
    {
        if ((stmt->kind == "let"))
        {
            py_get(env, stmt->name) = eval_expr(stmt->expr_index, expr_nodes, env);
            continue;
        }
        if ((stmt->kind == "assign"))
        {
            if ((!py_in(stmt->name, env)))
            {
                throw std::runtime_error(py_to_string(("assign to undefined variable: " + stmt->name)));
            }
            py_get(env, stmt->name) = eval_expr(stmt->expr_index, expr_nodes, env);
            continue;
        }
        long long value = eval_expr(stmt->expr_index, expr_nodes, env);
        if (trace)
        {
            py_print(value);
        }
        long long norm = py_mod(value, 1000000007);
        if ((norm < 0))
        {
            norm = (norm + 1000000007);
        }
        checksum = py_mod(((checksum * 131) + norm), 1000000007);
        printed = (printed + 1);
    }
    if (trace)
    {
        py_print("printed:", printed);
    }
    return checksum;
}

vector<string> build_benchmark_source(long long var_count, long long loops)
{
    vector<string> lines = {};
    auto __pytra_range_start_1 = 0;
    auto __pytra_range_stop_2 = var_count;
    auto __pytra_range_step_3 = 1;
    if (__pytra_range_step_3 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
    {
        lines.push_back(((("let v" + py_to_string(i)) + " = ") + py_to_string((i + 1))));
    }
    auto __pytra_range_start_4 = 0;
    auto __pytra_range_stop_5 = loops;
    auto __pytra_range_step_6 = 1;
    if (__pytra_range_step_6 == 0) throw std::runtime_error("range() arg 3 must not be zero");
    for (auto i = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (i < __pytra_range_stop_5) : (i > __pytra_range_stop_5); i += __pytra_range_step_6)
    {
        long long x = py_mod(i, var_count);
        long long y = py_mod((i + 3), var_count);
        long long c1 = (py_mod(i, 7) + 1);
        long long c2 = (py_mod(i, 11) + 2);
        lines.push_back(((((((((("v" + py_to_string(x)) + " = (v") + py_to_string(x)) + " * ") + py_to_string(c1)) + " + v") + py_to_string(y)) + " + 10000) / ") + py_to_string(c2)));
        if ((py_mod(i, 97) == 0))
        {
            lines.push_back(("print v" + py_to_string(x)));
        }
    }
    lines.push_back("print (v0 + v1 + v2 + v3)");
    return lines;
}

void run_demo()
{
    vector<string> demo_lines = {};
    demo_lines.push_back("let a = 10");
    demo_lines.push_back("let b = 3");
    demo_lines.push_back("a = (a + b) * 2");
    demo_lines.push_back("print a");
    demo_lines.push_back("print a / b");
    vector<pycs::gc::RcHandle<Token>> tokens = tokenize(demo_lines);
    pycs::gc::RcHandle<Parser> parser = pycs::gc::RcHandle<Parser>::adopt(pycs::gc::rc_new<Parser>(tokens));
    vector<pycs::gc::RcHandle<StmtNode>> stmts = parser->parse_program();
    long long checksum = execute(stmts, parser->expr_nodes, true);
    py_print("demo_checksum:", checksum);
}

void run_benchmark()
{
    vector<string> source_lines = build_benchmark_source(32, 120000);
    double start = perf_counter();
    vector<pycs::gc::RcHandle<Token>> tokens = tokenize(source_lines);
    pycs::gc::RcHandle<Parser> parser = pycs::gc::RcHandle<Parser>::adopt(pycs::gc::rc_new<Parser>(tokens));
    vector<pycs::gc::RcHandle<StmtNode>> stmts = parser->parse_program();
    long long checksum = execute(stmts, parser->expr_nodes, false);
    double elapsed = (perf_counter() - start);
    py_print("token_count:", py_len(tokens));
    py_print("expr_count:", py_len(parser->expr_nodes));
    py_print("stmt_count:", py_len(stmts));
    py_print("checksum:", checksum);
    py_print("elapsed_sec:", elapsed);
}

void py_main()
{
    run_demo();
    run_benchmark();
}

int main()
{
    py_main();
    return 0;
}
