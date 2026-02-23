// このファイルは EAST ベース Swift プレビュー出力です。
// TODO: 専用 SwiftEmitter 実装へ段階移行する。
import Foundation

func main() {
    /*
    using System;
    using System.Collections.Generic;
    using System.Linq;
    
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
        public List<Token> tokens;
        public long pos;
        public List<ExprNode> expr_nodes;
        
        public Parser(List<Token> tokens)
        {
            this.tokens = tokens;
            this.pos = 0;
            this.expr_nodes = this.new_expr_nodes();
        }
        
        public List<ExprNode> new_expr_nodes()
        {
            return new List<unknown>();
        }
        
        public string peek_kind()
        {
            return this.tokens[(int)(this.pos)].kind;
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
                Token t = this.tokens[(int)(this.pos)];
                throw RuntimeError(((((("parse error at pos=" + Convert.ToString(t.pos)) + ", expected=") + kind) + ", got=") + t.kind));
            }
            Token token = this.tokens[(int)(this.pos)];
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
            return ((this.expr_nodes).Count - 1);
        }
        
        public List<StmtNode> parse_program()
        {
            List<StmtNode> stmts = new List<unknown>();
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
                return this.add_expr(new ExprNode("neg", 0, "", "", child, (-1)));
            }
            return this.parse_primary();
        }
        
        public long parse_primary()
        {
            if (this.match("NUMBER")) {
                Token token_num = this.tokens[(int)((this.pos - 1))];
                return this.add_expr(new ExprNode("lit", Convert.ToInt64(token_num.text), "", "", (-1), (-1)));
            }
            if (this.match("IDENT")) {
                Token token_ident = this.tokens[(int)((this.pos - 1))];
                return this.add_expr(new ExprNode("var", 0, token_ident.text, "", (-1), (-1)));
            }
            if (this.match("LPAREN")) {
                long expr_index = this.parse_expr();
                this.expect("RPAREN");
                return expr_index;
            }
            Token t = this.tokens[(int)(this.pos)];
            throw RuntimeError(((("primary parse error at pos=" + Convert.ToString(t.pos)) + " got=") + t.kind));
        }
    }
    
    public static class Program
    {
        public static List<Token> tokenize(List<string> lines)
        {
            List<Token> tokens = new List<unknown>();
            foreach (var __it_1 in Program.PytraEnumerate(lines)) {
            var line_index = __it_1.Item1;
            var source = __it_1.Item2;
                long i = 0;
                long n = (source).Count();
                while (i < n) {
                    string ch = source[(int)(i)];
                    
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
                        while ((i < n) && source[(int)(i)].isdigit()) {
                            i += 1;
                        }
                        string text = source[(int)(null)];
                        tokens.Add(new Token("NUMBER", text, start));
                        py_continue;
                    }
                    if (ch.isalpha() || (ch == "_")) {
                        long start = i;
                        while ((i < n) && ((source[(int)(i)].isalpha() || (source[(int)(i)] == "_")) || source[(int)(i)].isdigit())) {
                            i += 1;
                        }
                        unknown text = source[(int)(null)];
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
                    throw RuntimeError(((((("tokenize error at line=" + Convert.ToString(line_index)) + " pos=") + Convert.ToString(i)) + " ch=") + ch));
                }
                tokens.Add(new Token("NEWLINE", "", n));
            }
            tokens.Add(new Token("EOF", "", (lines).Count));
            return tokens;
        }
        
        public static long eval_expr(long expr_index, List<ExprNode> expr_nodes, Dictionary<string, long> env)
        {
            ExprNode node = expr_nodes[(int)(expr_index)];
            
            if (node.kind == "lit") {
                return node.value;
            }
            if (node.kind == "var") {
                if (!(env.Contains(node.name))) {
                    throw RuntimeError(("undefined variable: " + node.name));
                }
                return env[(int)(node.name)];
            }
            if (node.kind == "neg") {
                return (-eval_expr(node.left, expr_nodes, env));
            }
            if (node.kind == "bin") {
                long lhs = eval_expr(node.left, expr_nodes, env);
                long rhs = eval_expr(node.right, expr_nodes, env);
                if (node.op == "+") {
                    return (lhs + rhs);
                }
                if (node.op == "-") {
                    return (lhs - rhs);
                }
                if (node.op == "*") {
                    return (lhs * rhs);
                }
                if (node.op == "/") {
                    if (rhs == 0) {
                        throw RuntimeError("division by zero");
                    }
                    return ((long)Math.Floor((double)(lhs) / (double)(rhs)));
                }
                throw RuntimeError(("unknown operator: " + node.op));
            }
            throw RuntimeError(("unknown node kind: " + node.kind));
        }
        
        public static long execute(List<StmtNode> stmts, List<ExprNode> expr_nodes, bool trace)
        {
            Dictionary<string, long> env = new Dictionary<unknown, unknown>();
            long checksum = 0;
            long printed = 0;
            
            foreach (var stmt in stmts) {
                if (stmt.kind == "let") {
                    env[(int)(stmt.name)] = eval_expr(stmt.expr_index, expr_nodes, env);
                    py_continue;
                }
                if (stmt.kind == "assign") {
                    if (!(env.Contains(stmt.name))) {
                        throw RuntimeError(("assign to undefined variable: " + stmt.name));
                    }
                    env[(int)(stmt.name)] = eval_expr(stmt.expr_index, expr_nodes, env);
                    py_continue;
                }
                long value = eval_expr(stmt.expr_index, expr_nodes, env);
                if (trace) {
                    Console.WriteLine(value);
                }
                long norm = (value % 1000000007);
                if (norm < 0) {
                    norm += 1000000007;
                }
                checksum = ((((checksum * 131) + norm)) % 1000000007);
                printed += 1;
            }
            if (trace) {
                Console.WriteLine(string.Join(" ", new object[] { "printed:", printed }));
            }
            return checksum;
        }
        
        public static List<string> build_benchmark_source(long var_count, long loops)
        {
            List<string> lines = new List<unknown>();
            
            // Declare initial variables.
            for (long i = 0; i < var_count; i += 1) {
                lines.Add(((("let v" + Convert.ToString(i)) + " = ") + Convert.ToString((i + 1))));
            }
            // Force evaluation of many arithmetic expressions.
            for (long i = 0; i < loops; i += 1) {
                long x = (i % var_count);
                long y = (((i + 3)) % var_count);
                long c1 = ((i % 7) + 1);
                long c2 = ((i % 11) + 2);
                lines.Add(((((((((("v" + Convert.ToString(x)) + " = (v") + Convert.ToString(x)) + " * ") + Convert.ToString(c1)) + " + v") + Convert.ToString(y)) + " + 10000) / ") + Convert.ToString(c2)));
                if ((i % 97) == 0) {
                    lines.Add(("print v" + Convert.ToString(x)));
                }
            }
            // Print final values together.
            lines.Add("print (v0 + v1 + v2 + v3)");
            return lines;
        }
        
        public static void run_demo()
        {
            List<string> demo_lines = new List<unknown>();
            demo_lines.Add("let a = 10");
            demo_lines.Add("let b = 3");
            demo_lines.Add("a = (a + b) * 2");
            demo_lines.Add("print a");
            demo_lines.Add("print a / b");
            
            List<Token> tokens = tokenize(demo_lines);
            Parser parser = new Parser(tokens);
            List<StmtNode> stmts = parser.parse_program();
            long checksum = execute(stmts, parser.expr_nodes, true);
            Console.WriteLine(string.Join(" ", new object[] { "demo_checksum:", checksum }));
        }
        
        public static void run_benchmark()
        {
            List<string> source_lines = build_benchmark_source(32, 120000);
            double start = perf_counter();
            List<Token> tokens = tokenize(source_lines);
            Parser parser = new Parser(tokens);
            List<StmtNode> stmts = parser.parse_program();
            long checksum = execute(stmts, parser.expr_nodes, false);
            double elapsed = (perf_counter() - start);
            
            Console.WriteLine(string.Join(" ", new object[] { "token_count:", (tokens).Count }));
            Console.WriteLine(string.Join(" ", new object[] { "expr_count:", (parser.expr_nodes).Count() }));
            Console.WriteLine(string.Join(" ", new object[] { "stmt_count:", (stmts).Count }));
            Console.WriteLine(string.Join(" ", new object[] { "checksum:", checksum }));
            Console.WriteLine(string.Join(" ", new object[] { "elapsed_sec:", elapsed }));
        }
        
        public static void __pytra_main()
        {
            run_demo();
            run_benchmark();
        }
        
        private static IEnumerable<(long, T)> PytraEnumerate<T>(IEnumerable<T> source, long start = 0)
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
    */
}

main()
