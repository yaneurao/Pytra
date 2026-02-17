using System.Collections.Generic;
using System.IO;
using System;

public static class Program
{
    public static List<Token> tokenize(List<string> lines)
    {
        List<Token> tokens = new List<Token> {  };
        long line_index = 0L;
        while (Pytra.CsModule.py_runtime.py_bool((line_index < Pytra.CsModule.py_runtime.py_len(lines))))
        {
            string source = Pytra.CsModule.py_runtime.py_get(lines, line_index);
            long i = 0L;
            long n = Pytra.CsModule.py_runtime.py_len(source);
            while (Pytra.CsModule.py_runtime.py_bool((i < n)))
            {
                string ch = Pytra.CsModule.py_runtime.py_slice(source, (long?)(i), (long?)((i + 1L)));
                if (Pytra.CsModule.py_runtime.py_bool((ch == " ")))
                {
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "+")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("PLUS", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "-")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("MINUS", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "*")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("STAR", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "/")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("SLASH", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "(")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("LPAREN", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == ")")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("RPAREN", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((ch == "=")))
                {
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("EQUAL", ch, i));
                    i = (i + 1L);
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool(Pytra.CsModule.py_runtime.py_isdigit(ch)))
                {
                    long start = i;
                    while (Pytra.CsModule.py_runtime.py_bool(((i < n) && Pytra.CsModule.py_runtime.py_isdigit(Pytra.CsModule.py_runtime.py_slice(source, (long?)(i), (long?)((i + 1L)))))))
                    {
                        i = (i + 1L);
                    }
                    string text = Pytra.CsModule.py_runtime.py_slice(source, (long?)(start), (long?)(i));
                    Pytra.CsModule.py_runtime.py_append(tokens, new Token("NUMBER", text, start));
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_isalpha(ch) || (ch == "_"))))
                {
                    var start = i;
                    while (Pytra.CsModule.py_runtime.py_bool(((i < n) && ((Pytra.CsModule.py_runtime.py_isalpha(Pytra.CsModule.py_runtime.py_slice(source, (long?)(i), (long?)((i + 1L)))) || (Pytra.CsModule.py_runtime.py_slice(source, (long?)(i), (long?)((i + 1L))) == "_")) || Pytra.CsModule.py_runtime.py_isdigit(Pytra.CsModule.py_runtime.py_slice(source, (long?)(i), (long?)((i + 1L))))))))
                    {
                        i = (i + 1L);
                    }
                    var text = Pytra.CsModule.py_runtime.py_slice(source, (long?)(start), (long?)(i));
                    if (Pytra.CsModule.py_runtime.py_bool((text == "let")))
                    {
                        Pytra.CsModule.py_runtime.py_append(tokens, new Token("LET", text, start));
                    }
                    else
                    {
                        if (Pytra.CsModule.py_runtime.py_bool((text == "print")))
                        {
                            Pytra.CsModule.py_runtime.py_append(tokens, new Token("PRINT", text, start));
                        }
                        else
                        {
                            Pytra.CsModule.py_runtime.py_append(tokens, new Token("IDENT", text, start));
                        }
                    }
                    continue;
                }
                throw new Exception(((((("tokenize error at line=" + Convert.ToString(line_index)) + " pos=") + Convert.ToString(i)) + " ch=") + ch));
            }
            Pytra.CsModule.py_runtime.py_append(tokens, new Token("NEWLINE", "", n));
            line_index = (line_index + 1L);
        }
        Pytra.CsModule.py_runtime.py_append(tokens, new Token("EOF", "", Pytra.CsModule.py_runtime.py_len(lines)));
        return tokens;
    }

    public static long eval_expr(long expr_index, List<ExprNode> expr_nodes, Dictionary<string, long> env)
    {
        ExprNode node = Pytra.CsModule.py_runtime.py_get(expr_nodes, expr_index);
        if (Pytra.CsModule.py_runtime.py_bool((node.kind == "lit")))
        {
            return node.value;
        }
        if (Pytra.CsModule.py_runtime.py_bool((node.kind == "var")))
        {
            if (Pytra.CsModule.py_runtime.py_bool((!Pytra.CsModule.py_runtime.py_in(node.name, env))))
            {
                throw new Exception(("undefined variable: " + node.name));
            }
            return Pytra.CsModule.py_runtime.py_get(env, node.name);
        }
        if (Pytra.CsModule.py_runtime.py_bool((node.kind == "neg")))
        {
            return (-eval_expr(node.left, expr_nodes, env));
        }
        if (Pytra.CsModule.py_runtime.py_bool((node.kind == "bin")))
        {
            long lhs = eval_expr(node.left, expr_nodes, env);
            long rhs = eval_expr(node.right, expr_nodes, env);
            if (Pytra.CsModule.py_runtime.py_bool((node.op == "+")))
            {
                return (lhs + rhs);
            }
            if (Pytra.CsModule.py_runtime.py_bool((node.op == "-")))
            {
                return (lhs - rhs);
            }
            if (Pytra.CsModule.py_runtime.py_bool((node.op == "*")))
            {
                return (lhs * rhs);
            }
            if (Pytra.CsModule.py_runtime.py_bool((node.op == "/")))
            {
                if (Pytra.CsModule.py_runtime.py_bool((rhs == 0L)))
                {
                    throw new Exception("division by zero");
                }
                return Pytra.CsModule.py_runtime.py_floordiv(lhs, rhs);
            }
            throw new Exception(("unknown operator: " + node.op));
        }
        throw new Exception(("unknown node kind: " + node.kind));
    }

    public static long execute(List<StmtNode> stmts, List<ExprNode> expr_nodes, bool trace)
    {
        Dictionary<string, long> env = new Dictionary<string, long>();
        long checksum = 0L;
        long printed = 0L;
        foreach (var stmt in stmts)
        {
            if (Pytra.CsModule.py_runtime.py_bool((stmt.kind == "let")))
            {
                Pytra.CsModule.py_runtime.py_set(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            if (Pytra.CsModule.py_runtime.py_bool((stmt.kind == "assign")))
            {
                if (Pytra.CsModule.py_runtime.py_bool((!Pytra.CsModule.py_runtime.py_in(stmt.name, env))))
                {
                    throw new Exception(("assign to undefined variable: " + stmt.name));
                }
                Pytra.CsModule.py_runtime.py_set(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            long value = eval_expr(stmt.expr_index, expr_nodes, env);
            if (Pytra.CsModule.py_runtime.py_bool(trace))
            {
                Pytra.CsModule.py_runtime.print(value);
            }
            long norm = Pytra.CsModule.py_runtime.py_mod(value, 1000000007L);
            if (Pytra.CsModule.py_runtime.py_bool((norm < 0L)))
            {
                norm = (norm + 1000000007L);
            }
            checksum = Pytra.CsModule.py_runtime.py_mod(((checksum * 131L) + norm), 1000000007L);
            printed = (printed + 1L);
        }
        if (Pytra.CsModule.py_runtime.py_bool(trace))
        {
            Pytra.CsModule.py_runtime.print("printed:", printed);
        }
        return checksum;
    }

    public static List<string> build_benchmark_source(long var_count, long loops)
    {
        List<string> lines = new List<string> {  };
        var __pytra_range_start_1 = 0;
        var __pytra_range_stop_2 = var_count;
        var __pytra_range_step_3 = 1;
        if (__pytra_range_step_3 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_1; (__pytra_range_step_3 > 0) ? (i < __pytra_range_stop_2) : (i > __pytra_range_stop_2); i += __pytra_range_step_3)
        {
            Pytra.CsModule.py_runtime.py_append(lines, ((("let v" + Convert.ToString(i)) + " = ") + Convert.ToString((i + 1L))));
        }
        var __pytra_range_start_4 = 0;
        var __pytra_range_stop_5 = loops;
        var __pytra_range_step_6 = 1;
        if (__pytra_range_step_6 == 0) throw new Exception("range() arg 3 must not be zero");
        for (var i = __pytra_range_start_4; (__pytra_range_step_6 > 0) ? (i < __pytra_range_stop_5) : (i > __pytra_range_stop_5); i += __pytra_range_step_6)
        {
            long x = Pytra.CsModule.py_runtime.py_mod(i, var_count);
            long y = Pytra.CsModule.py_runtime.py_mod((i + 3L), var_count);
            long c1 = (Pytra.CsModule.py_runtime.py_mod(i, 7L) + 1L);
            long c2 = (Pytra.CsModule.py_runtime.py_mod(i, 11L) + 2L);
            Pytra.CsModule.py_runtime.py_append(lines, ((((((((("v" + Convert.ToString(x)) + " = (v") + Convert.ToString(x)) + " * ") + Convert.ToString(c1)) + " + v") + Convert.ToString(y)) + " + 10000) / ") + Convert.ToString(c2)));
            if (Pytra.CsModule.py_runtime.py_bool((Pytra.CsModule.py_runtime.py_mod(i, 97L) == 0L)))
            {
                Pytra.CsModule.py_runtime.py_append(lines, ("print v" + Convert.ToString(x)));
            }
        }
        Pytra.CsModule.py_runtime.py_append(lines, "print (v0 + v1 + v2 + v3)");
        return lines;
    }

    public static void run_demo()
    {
        List<string> demo_lines = new List<string> {  };
        Pytra.CsModule.py_runtime.py_append(demo_lines, "let a = 10");
        Pytra.CsModule.py_runtime.py_append(demo_lines, "let b = 3");
        Pytra.CsModule.py_runtime.py_append(demo_lines, "a = (a + b) * 2");
        Pytra.CsModule.py_runtime.py_append(demo_lines, "print a");
        Pytra.CsModule.py_runtime.py_append(demo_lines, "print a / b");
        List<Token> tokens = tokenize(demo_lines);
        Parser parser = new Parser(tokens);
        List<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, true);
        Pytra.CsModule.py_runtime.print("demo_checksum:", checksum);
    }

    public static void run_benchmark()
    {
        List<string> source_lines = build_benchmark_source(32L, 120000L);
        double start = Pytra.CsModule.time.perf_counter();
        List<Token> tokens = tokenize(source_lines);
        Parser parser = new Parser(tokens);
        List<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, false);
        double elapsed = (Pytra.CsModule.time.perf_counter() - start);
        Pytra.CsModule.py_runtime.print("token_count:", Pytra.CsModule.py_runtime.py_len(tokens));
        Pytra.CsModule.py_runtime.print("expr_count:", Pytra.CsModule.py_runtime.py_len(parser.expr_nodes));
        Pytra.CsModule.py_runtime.print("stmt_count:", Pytra.CsModule.py_runtime.py_len(stmts));
        Pytra.CsModule.py_runtime.print("checksum:", checksum);
        Pytra.CsModule.py_runtime.print("elapsed_sec:", elapsed);
    }

    public static void main()
    {
        run_demo();
        run_benchmark();
    }

    public class Token
    {
        public string kind;
        public string text;
        public long pos;
        public Token(string kind, string text, long pos)
        {
            this.kind = kind;
            this.text = text;
            this.pos = pos;
        }

    }

    public class ExprNode
    {
        public string kind;
        public long value;
        public string name;
        public string op;
        public long left;
        public long right;
        public ExprNode(string kind, long value, string name, string op, long left, long right)
        {
            this.kind = kind;
            this.value = value;
            this.name = name;
            this.op = op;
            this.left = left;
            this.right = right;
        }

    }

    public class StmtNode
    {
        public string kind;
        public string name;
        public long expr_index;
        public StmtNode(string kind, string name, long expr_index)
        {
            this.kind = kind;
            this.name = name;
            this.expr_index = expr_index;
        }

    }

    public class Parser
    {
        public List<Token> tokens;
        public long pos;
        public List<ExprNode> expr_nodes;

        public List<ExprNode> new_expr_nodes()
        {
            List<ExprNode> nodes = new List<ExprNode> {  };
            return nodes;
        }
        public Parser(List<Token> tokens)
        {
            this.tokens = tokens;
            this.pos = 0L;
            this.expr_nodes = this.new_expr_nodes();
        }
        public string peek_kind()
        {
            return Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos).kind;
        }
        public bool match(string kind)
        {
            if (Pytra.CsModule.py_runtime.py_bool((this.peek_kind() == kind)))
            {
                this.pos = (this.pos + 1L);
                return true;
            }
            return false;
        }
        public Token expect(string kind)
        {
            if (Pytra.CsModule.py_runtime.py_bool((this.peek_kind() != kind)))
            {
                Token t = Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos);
                throw new Exception(((((("parse error at pos=" + Convert.ToString(t.pos)) + ", expected=") + kind) + ", got=") + t.kind));
            }
            Token token = Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos);
            this.pos = (this.pos + 1L);
            return token;
        }
        public void skip_newlines()
        {
            while (Pytra.CsModule.py_runtime.py_bool(this.match("NEWLINE")))
            {
            }
        }
        public long add_expr(ExprNode node)
        {
            Pytra.CsModule.py_runtime.py_append(this.expr_nodes, node);
            return (Pytra.CsModule.py_runtime.py_len(this.expr_nodes) - 1L);
        }
        public List<StmtNode> parse_program()
        {
            List<StmtNode> stmts = new List<StmtNode> {  };
            this.skip_newlines();
            while (Pytra.CsModule.py_runtime.py_bool((this.peek_kind() != "EOF")))
            {
                StmtNode stmt = this.parse_stmt();
                Pytra.CsModule.py_runtime.py_append(stmts, stmt);
                this.skip_newlines();
            }
            return stmts;
        }
        public StmtNode parse_stmt()
        {
            if (Pytra.CsModule.py_runtime.py_bool(this.match("LET")))
            {
                string let_name = this.expect("IDENT").text;
                this.expect("EQUAL");
                long let_expr_index = this.parse_expr();
                return new StmtNode("let", let_name, let_expr_index);
            }
            if (Pytra.CsModule.py_runtime.py_bool(this.match("PRINT")))
            {
                long print_expr_index = this.parse_expr();
                return new StmtNode("print", "", print_expr_index);
            }
            string assign_name = this.expect("IDENT").text;
            this.expect("EQUAL");
            long assign_expr_index = this.parse_expr();
            return new StmtNode("assign", assign_name, assign_expr_index);
        }
        public long parse_expr()
        {
            return this.parse_add();
        }
        public long parse_add()
        {
            long left = this.parse_mul();
            bool done = false;
            while (Pytra.CsModule.py_runtime.py_bool((!done)))
            {
                if (Pytra.CsModule.py_runtime.py_bool(this.match("PLUS")))
                {
                    long right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "+", left, right));
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool(this.match("MINUS")))
                {
                    var right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "-", left, right));
                    continue;
                }
                done = true;
            }
            return left;
        }
        public long parse_mul()
        {
            long left = this.parse_unary();
            bool done = false;
            while (Pytra.CsModule.py_runtime.py_bool((!done)))
            {
                if (Pytra.CsModule.py_runtime.py_bool(this.match("STAR")))
                {
                    long right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "*", left, right));
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_bool(this.match("SLASH")))
                {
                    var right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "/", left, right));
                    continue;
                }
                done = true;
            }
            return left;
        }
        public long parse_unary()
        {
            if (Pytra.CsModule.py_runtime.py_bool(this.match("MINUS")))
            {
                long child = this.parse_unary();
                return this.add_expr(new ExprNode("neg", 0L, "", "", child, (-1L)));
            }
            return this.parse_primary();
        }
        public long parse_primary()
        {
            if (Pytra.CsModule.py_runtime.py_bool(this.match("NUMBER")))
            {
                Token token_num = Pytra.CsModule.py_runtime.py_get(this.tokens, (this.pos - 1L));
                return this.add_expr(new ExprNode("lit", Pytra.CsModule.py_runtime.py_int(token_num.text), "", "", (-1L), (-1L)));
            }
            if (Pytra.CsModule.py_runtime.py_bool(this.match("IDENT")))
            {
                Token token_ident = Pytra.CsModule.py_runtime.py_get(this.tokens, (this.pos - 1L));
                return this.add_expr(new ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L)));
            }
            if (Pytra.CsModule.py_runtime.py_bool(this.match("LPAREN")))
            {
                long expr_index = this.parse_expr();
                this.expect("RPAREN");
                return expr_index;
            }
            var t = Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos);
            throw new Exception(((("primary parse error at pos=" + Convert.ToString(t.pos)) + " got=") + t.kind));
        }
    }

    public static void Main(string[] args)
    {
        main();
    }
}
