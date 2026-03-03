using System;
using System.Collections.Generic;
using System.Linq;
using Any = System.Object;
using int64 = System.Int64;
using float64 = System.Double;
using str = System.String;
using Pytra.CsModule;

public class Token
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string kind;
    public string text;
    public long pos;
    public long number_value;
    
    public Token(string kind, string text, long pos, long number_value)
    {
        this.kind = kind;
        this.text = text;
        this.pos = pos;
        this.number_value = number_value;
    }
}

public class ExprNode
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string kind;
    public long value;
    public string name;
    public string op;
    public long left;
    public long right;
    public long kind_tag;
    public long op_tag;
    
    public ExprNode(string kind, long value, string name, string op, long left, long right, long kind_tag, long op_tag)
    {
        this.kind = kind;
        this.value = value;
        this.name = name;
        this.op = op;
        this.left = left;
        this.right = right;
        this.kind_tag = kind_tag;
        this.op_tag = op_tag;
    }
}

public class StmtNode
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public string kind;
    public string name;
    public long expr_index;
    public long kind_tag;
    
    public StmtNode(string kind, string name, long expr_index, long kind_tag)
    {
        this.kind = kind;
        this.name = name;
        this.expr_index = expr_index;
        this.kind_tag = kind_tag;
    }
}

public class Parser
{
    public static readonly long PYTRA_TYPE_ID = Pytra.CsModule.py_runtime.py_register_class_type(Pytra.CsModule.py_runtime.PYTRA_TID_OBJECT);
    public System.Collections.Generic.List<Token> tokens;
    public long pos;
    public System.Collections.Generic.List<ExprNode> expr_nodes;
    
    public Parser(System.Collections.Generic.List<Token> tokens)
    {
        this.tokens = new System.Collections.Generic.List<Token>(tokens);
        this.pos = 0;
        this.expr_nodes = this.new_expr_nodes();
    }
    
    public System.Collections.Generic.List<ExprNode> new_expr_nodes()
    {
        return new System.Collections.Generic.List<ExprNode>();
    }
    
    public Token current_token()
    {
        return Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos);
    }
    
    public Token previous_token()
    {
        return Pytra.CsModule.py_runtime.py_get(this.tokens, this.pos - 1);
    }
    
    public string peek_kind()
    {
        return this.current_token().kind;
    }
    
    public bool match(string kind)
    {
        if (this.peek_kind() == kind) {
            this.pos += 1;
            return true;
        }
        return false;
    }
    
    public Token expect(string kind)
    {
        Token token = this.current_token();
        if (token.kind != kind) {
            throw new System.Exception("parse error at pos=" + System.Convert.ToString(token.pos) + ", expected=" + kind + ", got=" + token.kind);
        }
        this.pos += 1;
        return token;
    }
    
    public void skip_newlines()
    {
        while (this.match("NEWLINE")) {
            ;
        }
    }
    
    public long add_expr(ExprNode node)
    {
        this.expr_nodes.Add(node);
        return (this.expr_nodes).Count - 1;
    }
    
    public System.Collections.Generic.List<StmtNode> parse_program()
    {
        System.Collections.Generic.List<StmtNode> stmts = new System.Collections.Generic.List<StmtNode>();
        this.skip_newlines();
        while (this.peek_kind() != "EOF") {
            StmtNode stmt = this.parse_stmt();
            stmts.Add(stmt);
            this.skip_newlines();
        }
        return stmts;
    }
    
    public StmtNode parse_stmt()
    {
        if (this.match("LET")) {
            string let_name = System.Convert.ToString(this.expect("IDENT").text);
            this.expect("EQUAL");
            long let_expr_index = this.parse_expr();
            return new StmtNode("let", let_name, let_expr_index, 1);
        }
        if (this.match("PRINT")) {
            long print_expr_index = this.parse_expr();
            return new StmtNode("print", "", print_expr_index, 3);
        }
        string assign_name = System.Convert.ToString(this.expect("IDENT").text);
        this.expect("EQUAL");
        long assign_expr_index = this.parse_expr();
        return new StmtNode("assign", assign_name, assign_expr_index, 2);
    }
    
    public long parse_expr()
    {
        return this.parse_add();
    }
    
    public long parse_add()
    {
        long left = this.parse_mul();
        while (true) {
            if (this.match("PLUS")) {
                long right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "+", left, right, 3, 1));
                continue;
            }
            if (this.match("MINUS")) {
                long right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "-", left, right, 3, 2));
                continue;
            }
            break;
        }
        return left;
    }
    
    public long parse_mul()
    {
        long left = this.parse_unary();
        while (true) {
            if (this.match("STAR")) {
                long right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "*", left, right, 3, 3));
                continue;
            }
            if (this.match("SLASH")) {
                long right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "/", left, right, 3, 4));
                continue;
            }
            break;
        }
        return left;
    }
    
    public long parse_unary()
    {
        if (this.match("MINUS")) {
            long child = this.parse_unary();
            return this.add_expr(new ExprNode("neg", 0, "", "", child, -1, 4, 0));
        }
        return this.parse_primary();
    }
    
    public long parse_primary()
    {
        if (this.match("NUMBER")) {
            Token token_num = this.previous_token();
            return this.add_expr(new ExprNode("lit", token_num.number_value, "", "", -1, -1, 1, 0));
        }
        if (this.match("IDENT")) {
            Token token_ident = this.previous_token();
            return this.add_expr(new ExprNode("var", 0, token_ident.text, "", -1, -1, 2, 0));
        }
        if (this.match("LPAREN")) {
            long expr_index = this.parse_expr();
            this.expect("RPAREN");
            return expr_index;
        }
        Token t = this.current_token();
        throw new System.Exception("primary parse error at pos=" + System.Convert.ToString(t.pos) + " got=" + t.kind);
    return default(long);
    }
}

public static class Program
{
    public static System.Collections.Generic.List<Token> tokenize(System.Collections.Generic.List<string> lines)
    {
        System.Collections.Generic.Dictionary<string, long> single_char_token_tags = new System.Collections.Generic.Dictionary<string, long> { { "+", 1 }, { "-", 2 }, { "*", 3 }, { "/", 4 }, { "(", 5 }, { ")", 6 }, { "=", 7 } };
        System.Collections.Generic.List<string> single_char_token_kinds = new System.Collections.Generic.List<string> { "PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL" };
        System.Collections.Generic.List<Token> tokens = new System.Collections.Generic.List<Token>();
        foreach (var __it_1 in Program.PytraEnumerate(lines)) {
        var line_index = __it_1.Item1;
        var source = __it_1.Item2;
            long i = 0;
            long n = (source).Length;
            while (i < n) {
                string ch = Pytra.CsModule.py_runtime.py_get(source, i);
                
                if (ch == " ") {
                    i += 1;
                    continue;
                }
                long single_tag = System.Convert.ToInt64((single_char_token_tags.ContainsKey(System.Convert.ToString(ch)) ? single_char_token_tags[System.Convert.ToString(ch)] : 0));
                if (single_tag > 0) {
                    tokens.Add(new Token(Pytra.CsModule.py_runtime.py_get(single_char_token_kinds, single_tag - 1), ch, i, 0));
                    i += 1;
                    continue;
                }
                if (Pytra.CsModule.py_runtime.py_isdigit(ch)) {
                    long start = i;
                    while ((i < n) && (Pytra.CsModule.py_runtime.py_isdigit(Pytra.CsModule.py_runtime.py_get(source, i)))) {
                        i += 1;
                    }
                    string text = Pytra.CsModule.py_runtime.py_slice(source, System.Convert.ToInt64(start), System.Convert.ToInt64(i));
                    tokens.Add(new Token("NUMBER", text, start, Pytra.CsModule.py_runtime.py_int(text)));
                    continue;
                }
                if ((Pytra.CsModule.py_runtime.py_isalpha(ch)) || (ch == "_")) {
                    long start = i;
                    while ((i < n) && (((((Pytra.CsModule.py_runtime.py_isalpha(Pytra.CsModule.py_runtime.py_get(source, i))) || (Pytra.CsModule.py_runtime.py_get(source, i) == "_"))) || (Pytra.CsModule.py_runtime.py_isdigit(Pytra.CsModule.py_runtime.py_get(source, i)))))) {
                        i += 1;
                    }
                    string text = Pytra.CsModule.py_runtime.py_slice(source, System.Convert.ToInt64(start), System.Convert.ToInt64(i));
                    if (text == "let") {
                        tokens.Add(new Token("LET", text, start, 0));
                    } else {
                        if (text == "print") {
                            tokens.Add(new Token("PRINT", text, start, 0));
                        } else {
                            tokens.Add(new Token("IDENT", text, start, 0));
                        }
                    }
                    continue;
                }
                throw new System.Exception("tokenize error at line=" + System.Convert.ToString(line_index) + " pos=" + System.Convert.ToString(i) + " ch=" + ch);
            }
            tokens.Add(new Token("NEWLINE", "", n, 0));
        }
        tokens.Add(new Token("EOF", "", (lines).Count, 0));
        return tokens;
    }
    
    public static long eval_expr(long expr_index, System.Collections.Generic.List<ExprNode> expr_nodes, System.Collections.Generic.Dictionary<string, long> env)
    {
        ExprNode node = Pytra.CsModule.py_runtime.py_get(expr_nodes, expr_index);
        
        if (node.kind_tag == 1) {
            return node.value;
        }
        if (node.kind_tag == 2) {
            if (!((env).ContainsKey(node.name))) {
                throw new System.Exception("undefined variable: " + node.name);
            }
            return env[node.name];
        }
        if (node.kind_tag == 4) {
            return -eval_expr(node.left, expr_nodes, env);
        }
        if (node.kind_tag == 3) {
            long lhs = eval_expr(node.left, expr_nodes, env);
            long rhs = eval_expr(node.right, expr_nodes, env);
            if (node.op_tag == 1) {
                return lhs + rhs;
            }
            if (node.op_tag == 2) {
                return lhs - rhs;
            }
            if (node.op_tag == 3) {
                return lhs * rhs;
            }
            if (node.op_tag == 4) {
                if (rhs == 0) {
                    throw new System.Exception("division by zero");
                }
                return System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(lhs) / System.Convert.ToDouble(rhs)));
            }
            throw new System.Exception("unknown operator: " + node.op);
        }
        throw new System.Exception("unknown node kind: " + node.kind);
    return default(long);
    }
    
    public static long execute(System.Collections.Generic.List<StmtNode> stmts, System.Collections.Generic.List<ExprNode> expr_nodes, bool trace)
    {
        System.Collections.Generic.Dictionary<string, long> env = new System.Collections.Generic.Dictionary<string, long>();
        long checksum = 0;
        long printed = 0;
        
        foreach (var stmt in stmts) {
            if (stmt.kind_tag == 1) {
                env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
                continue;
            }
            if (stmt.kind_tag == 2) {
                if (!((env).ContainsKey(stmt.name))) {
                    throw new System.Exception("assign to undefined variable: " + stmt.name);
                }
                env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env);
                continue;
            }
            long value = eval_expr(stmt.expr_index, expr_nodes, env);
            if (trace) {
                System.Console.WriteLine(value);
            }
            long norm = value % 1000000007;
            if (norm < 0) {
                norm += 1000000007;
            }
            checksum = (checksum * 131 + norm) % 1000000007;
            printed += 1;
        }
        if (trace) {
            System.Console.WriteLine(string.Join(" ", new object[] { "printed:", printed }));
        }
        return checksum;
    }
    
    public static System.Collections.Generic.List<string> build_benchmark_source(long var_count, long loops)
    {
        System.Collections.Generic.List<string> lines = new System.Collections.Generic.List<string>();
        
        // Declare initial variables.
        long i = 0;
        for (i = 0; i < var_count; i += 1) {
            lines.Add("let v" + System.Convert.ToString(i) + " = " + System.Convert.ToString(i + 1));
        }
        // Force evaluation of many arithmetic expressions.
        for (i = 0; i < loops; i += 1) {
            long x = i % var_count;
            long y = (i + 3) % var_count;
            long c1 = i % 7 + 1;
            long c2 = i % 11 + 2;
            lines.Add("v" + System.Convert.ToString(x) + " = (v" + System.Convert.ToString(x) + " * " + System.Convert.ToString(c1) + " + v" + System.Convert.ToString(y) + " + 10000) / " + System.Convert.ToString(c2));
            if (i % 97 == 0) {
                lines.Add("print v" + System.Convert.ToString(x));
            }
        }
        // Print final values together.
        lines.Add("print (v0 + v1 + v2 + v3)");
        return lines;
    }
    
    public static void run_demo()
    {
        System.Collections.Generic.List<string> demo_lines = new System.Collections.Generic.List<string>();
        demo_lines.Add("let a = 10");
        demo_lines.Add("let b = 3");
        demo_lines.Add("a = (a + b) * 2");
        demo_lines.Add("print a");
        demo_lines.Add("print a / b");
        
        System.Collections.Generic.List<Token> tokens = tokenize(demo_lines);
        Parser parser = new Parser(tokens);
        System.Collections.Generic.List<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, true);
        System.Console.WriteLine(string.Join(" ", new object[] { "demo_checksum:", checksum }));
    }
    
    public static void run_benchmark()
    {
        System.Collections.Generic.List<string> source_lines = build_benchmark_source(32, 120000);
        double start = Pytra.CsModule.time.perf_counter();
        System.Collections.Generic.List<Token> tokens = tokenize(source_lines);
        Parser parser = new Parser(tokens);
        System.Collections.Generic.List<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, false);
        double elapsed = Pytra.CsModule.time.perf_counter() - start;
        
        System.Console.WriteLine(string.Join(" ", new object[] { "token_count:", (tokens).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "expr_count:", (parser.expr_nodes).Count() }));
        System.Console.WriteLine(string.Join(" ", new object[] { "stmt_count:", (stmts).Count }));
        System.Console.WriteLine(string.Join(" ", new object[] { "checksum:", checksum }));
        System.Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
    }
    
    public static void __pytra_main()
    {
        run_demo();
        run_benchmark();
    }
    
    public static void Main(string[] args)
    {
            __pytra_main();
    }
    
    public static System.Collections.Generic.IEnumerable<(long, T)> PytraEnumerate<T>(System.Collections.Generic.IEnumerable<T> source, long start = 0)
    {
        long i = start;
        foreach (T item in source)
        {
            yield return (i, item);
            i += 1;
        }
    }
}
