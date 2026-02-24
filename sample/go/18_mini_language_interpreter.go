public class Token
{
    public string kind;
    public string text;
    public long pos;
    public static string kind;
    public static string text;
    public static long pos;
}

public class ExprNode
{
    public string kind;
    public long value;
    public string name;
    public string op;
    public long left;
    public long right;
    public static string kind;
    public static long value;
    public static string name;
    public static string op;
    public static long left;
    public static long right;
}

public class StmtNode
{
    public string kind;
    public string name;
    public long expr_index;
    public static string kind;
    public static string name;
    public static long expr_index;
}

public class Parser
{
    public System.Collections.Generic.List<Token> tokens;
    public long pos;
    public System.Collections.Generic.List<ExprNode> expr_nodes;
    
    public Parser(System.Collections.Generic.List<Token> tokens)
    {
        this.tokens = tokens;
        this.pos = 0;
        this.expr_nodes = this.new_expr_nodes();
    }
    
    public System.Collections.Generic.List<ExprNode> new_expr_nodes()
    {
        return new System.Collections.Generic.List<unknown>();
    }
    
    public string peek_kind()
    {
        return this.tokens[System.Convert.ToInt32(this.pos)].kind;
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
        if (this.peek_kind() != kind) {
            Token t = this.tokens[System.Convert.ToInt32(this.pos)];
            throw RuntimeError("parse error at pos=" + System.Convert.ToString(t.pos) + ", expected=" + kind + ", got=" + t.kind);
        }
        Token token = this.tokens[System.Convert.ToInt32(this.pos)];
        this.pos += 1;
        return token;
    }
    
    public void skip_newlines()
    {
        while (this.match("NEWLINE")) {
            // pass
        }
    }
    
    public long add_expr(ExprNode node)
    {
        this.expr_nodes.Add(node);
        return (this.expr_nodes).Count - 1;
    }
    
    public System.Collections.Generic.List<StmtNode> parse_program()
    {
        System.Collections.Generic.List<StmtNode> stmts = new System.Collections.Generic.List<unknown>();
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
            string let_name = this.expect("IDENT").text;
            this.expect("EQUAL");
            long let_expr_index = this.parse_expr();
            return new StmtNode("let", let_name, let_expr_index);
        }
        if (this.match("PRINT")) {
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
        while (true) {
            if (this.match("PLUS")) {
                long right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "+", left, right));
                py_continue;
            }
            if (this.match("MINUS")) {
                long right = this.parse_mul();
                left = this.add_expr(new ExprNode("bin", 0, "", "-", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    public long parse_mul()
    {
        long left = this.parse_unary();
        while (true) {
            if (this.match("STAR")) {
                long right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "*", left, right));
                py_continue;
            }
            if (this.match("SLASH")) {
                long right = this.parse_unary();
                left = this.add_expr(new ExprNode("bin", 0, "", "/", left, right));
                py_continue;
            }
            py_break;
        }
        return left;
    }
    
    public long parse_unary()
    {
        if (this.match("MINUS")) {
            long child = this.parse_unary();
            return this.add_expr(new ExprNode("neg", 0, "", "", child, -1));
        }
        return this.parse_primary();
    }
    
    public long parse_primary()
    {
        if (this.match("NUMBER")) {
            Token token_num = this.tokens[System.Convert.ToInt32(this.pos - 1)];
            return this.add_expr(new ExprNode("lit", System.Convert.ToInt64(token_num.text), "", "", -1, -1));
        }
        if (this.match("IDENT")) {
            Token token_ident = this.tokens[System.Convert.ToInt32(this.pos - 1)];
            return this.add_expr(new ExprNode("var", 0, token_ident.text, "", -1, -1));
        }
        if (this.match("LPAREN")) {
            long expr_index = this.parse_expr();
            this.expect("RPAREN");
            return expr_index;
        }
        Token t = this.tokens[System.Convert.ToInt32(this.pos)];
        throw RuntimeError("primary parse error at pos=" + System.Convert.ToString(t.pos) + " got=" + t.kind);
    }
}

public static class Program
{
    public static System.Collections.Generic.List<Token> tokenize(System.Collections.Generic.List<string> lines)
    {
        System.Collections.Generic.List<Token> tokens = new System.Collections.Generic.List<unknown>();
        foreach (var __it_1 in Program.PytraEnumerate(lines)) {
        var line_index = __it_1.Item1;
        var source = __it_1.Item2;
            long i = 0;
            long n = (source).Count();
            while (i < n) {
                string ch = source[System.Convert.ToInt32(i)];
                
                if (ch == " ") {
                    i += 1;
                    py_continue;
                }
                if (ch == "+") {
                    tokens.Add(new Token("PLUS", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == "-") {
                    tokens.Add(new Token("MINUS", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == "*") {
                    tokens.Add(new Token("STAR", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == "/") {
                    tokens.Add(new Token("SLASH", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == "(") {
                    tokens.Add(new Token("LPAREN", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == ")") {
                    tokens.Add(new Token("RPAREN", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch == "=") {
                    tokens.Add(new Token("EQUAL", ch, i));
                    i += 1;
                    py_continue;
                }
                if (ch.isdigit()) {
                    long start = i;
                    while (i < n && source[System.Convert.ToInt32(i)].isdigit()) {
                        i += 1;
                    }
                    string text = source[System.Convert.ToInt32(null)];
                    tokens.Add(new Token("NUMBER", text, start));
                    py_continue;
                }
                if (ch.isalpha() || ch == "_") {
                    long start = i;
                    while (i < n && source[System.Convert.ToInt32(i)].isalpha() || source[System.Convert.ToInt32(i)] == "_" || source[System.Convert.ToInt32(i)].isdigit()) {
                        i += 1;
                    }
                    unknown text = source[System.Convert.ToInt32(null)];
                    if (text == "let") {
                        tokens.Add(new Token("LET", text, start));
                    } else {
                        if (text == "print") {
                            tokens.Add(new Token("PRINT", text, start));
                        } else {
                            tokens.Add(new Token("IDENT", text, start));
                        }
                    }
                    py_continue;
                }
                throw RuntimeError("tokenize error at line=" + System.Convert.ToString(line_index) + " pos=" + System.Convert.ToString(i) + " ch=" + ch);
            }
            tokens.Add(new Token("NEWLINE", "", n));
        }
        tokens.Add(new Token("EOF", "", (lines).Count));
        return tokens;
    }
    
    public static long eval_expr(long expr_index, System.Collections.Generic.List<ExprNode> expr_nodes, System.Collections.Generic.Dictionary<string, long> env)
    {
        ExprNode node = expr_nodes[System.Convert.ToInt32(expr_index)];
        
        if (node.kind == "lit") {
            return node.value;
        }
        if (node.kind == "var") {
            if (!(env.Contains(node.name))) {
                throw RuntimeError("undefined variable: " + node.name);
            }
            return env[System.Convert.ToInt32(node.name)];
        }
        if (node.kind == "neg") {
            return -eval_expr(node.left, expr_nodes, env);
        }
        if (node.kind == "bin") {
            long lhs = eval_expr(node.left, expr_nodes, env);
            long rhs = eval_expr(node.right, expr_nodes, env);
            if (node.op == "+") {
                return lhs + rhs;
            }
            if (node.op == "-") {
                return lhs - rhs;
            }
            if (node.op == "*") {
                return lhs * rhs;
            }
            if (node.op == "/") {
                if (rhs == 0) {
                    throw RuntimeError("division by zero");
                }
                return System.Convert.ToInt64(System.Math.Floor(System.Convert.ToDouble(lhs) / System.Convert.ToDouble(rhs)));
            }
            throw RuntimeError("unknown operator: " + node.op);
        }
        throw RuntimeError("unknown node kind: " + node.kind);
    }
    
    public static long execute(System.Collections.Generic.List<StmtNode> stmts, System.Collections.Generic.List<ExprNode> expr_nodes, bool trace)
    {
        System.Collections.Generic.Dictionary<string, long> env = new System.Collections.Generic.Dictionary<unknown, unknown>();
        long checksum = 0;
        long printed = 0;
        foreach (var stmt in stmts) {
            if (stmt.kind == "let") {
                env[System.Convert.ToInt32(stmt.name)] = eval_expr(stmt.expr_index, expr_nodes, env);
                py_continue;
            }
            if (stmt.kind == "assign") {
                if (!(env.Contains(stmt.name))) {
                    throw RuntimeError("assign to undefined variable: " + stmt.name);
                }
                env[System.Convert.ToInt32(stmt.name)] = eval_expr(stmt.expr_index, expr_nodes, env);
                py_continue;
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
        System.Collections.Generic.List<string> lines = new System.Collections.Generic.List<unknown>();
        for (long i = 0; i < var_count; i += 1) {
            lines.Add("let v" + System.Convert.ToString(i) + " = " + System.Convert.ToString(i + 1));
        }
        for (long i = 0; i < loops; i += 1) {
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
        System.Collections.Generic.List<string> demo_lines = new System.Collections.Generic.List<unknown>();
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
        double start = perf_counter();
        System.Collections.Generic.List<Token> tokens = tokenize(source_lines);
        Parser parser = new Parser(tokens);
        System.Collections.Generic.List<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, false);
        double elapsed = perf_counter() - start;
        
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
    
    private static System.Collections.Generic.IEnumerable<(long, T)> PytraEnumerate<T>(System.Collections.Generic.IEnumerable<T> source, long start = 0)
    {
        long i = start;
        foreach (T item in source)
        {
            yield return (i, item);
            i += 1;
        }
    }
    
    public static void Main(string[] args)
    {
            main();
    }
}
