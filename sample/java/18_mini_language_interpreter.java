public final class Pytra_18_mini_language_interpreter {
    private Pytra_18_mini_language_interpreter() {
    }


    public static class Token {
        public String kind;
        public String text;
        public long pos;
        public Token() {
        }

        public Token(String kind, String text, long pos) {
            this.kind = kind;
            this.text = text;
            this.pos = pos;
        }
    }

    public static class ExprNode {
        public String kind;
        public long value;
        public String name;
        public String op;
        public long left;
        public long right;
        public ExprNode() {
        }

        public ExprNode(String kind, long value, String name, String op, long left, long right) {
            this.kind = kind;
            this.value = value;
            this.name = name;
            this.op = op;
            this.left = left;
            this.right = right;
        }
    }

    public static class StmtNode {
        public String kind;
        public String name;
        public long expr_index;
        public StmtNode() {
        }

        public StmtNode(String kind, String name, long expr_index) {
            this.kind = kind;
            this.name = name;
            this.expr_index = expr_index;
        }
    }

    public static class Parser {
        public java.util.ArrayList<Object> tokens;
        public long pos;
        public java.util.ArrayList<Object> expr_nodes;

        public java.util.ArrayList<Object> new_expr_nodes() {
            return new java.util.ArrayList<Object>(java.util.Arrays.asList());
        }

        public Parser(java.util.ArrayList<Object> tokens) {
            this.tokens = tokens;
            this.pos = 0L;
            this.expr_nodes = this.new_expr_nodes();
        }

        public String peek_kind() {
            return ((Token)(this.tokens.get((int)((((this.pos) < 0L) ? (((long)(this.tokens.size())) + (this.pos)) : (this.pos)))))).kind;
        }

        public boolean match(String kind) {
            if ((java.util.Objects.equals(this.peek_kind(), kind))) {
                this.pos += 1L;
                return true;
            }
            return false;
        }

        public Token expect(String kind) {
            if ((!(java.util.Objects.equals(this.peek_kind(), kind)))) {
                Token t = ((Token)(this.tokens.get((int)((((this.pos) < 0L) ? (((long)(this.tokens.size())) + (this.pos)) : (this.pos))))));
                throw new RuntimeException(__pytra_str(new RuntimeError(((((("parse error at pos=" + String.valueOf(t.pos)) + ", expected=") + kind) + ", got=") + t.kind))));
            }
            Token token = ((Token)(this.tokens.get((int)((((this.pos) < 0L) ? (((long)(this.tokens.size())) + (this.pos)) : (this.pos))))));
            this.pos += 1L;
            return token;
        }

        public void skip_newlines() {
            while (this.match("NEWLINE")) {
                ;
            }
        }

        public long add_expr(ExprNode node) {
            this.expr_nodes.add(node);
            return (((long)(this.expr_nodes.size())) - 1L);
        }

        public java.util.ArrayList<Object> parse_program() {
            java.util.ArrayList<Object> stmts = new java.util.ArrayList<Object>(java.util.Arrays.asList());
            this.skip_newlines();
            while ((!(java.util.Objects.equals(this.peek_kind(), "EOF")))) {
                StmtNode stmt = this.parse_stmt();
                stmts.add(stmt);
                this.skip_newlines();
            }
            return stmts;
        }

        public StmtNode parse_stmt() {
            if (this.match("LET")) {
                String let_name = this.expect("IDENT").text;
                this.expect("EQUAL");
                long let_expr_index = this.parse_expr();
                return new StmtNode("let", let_name, let_expr_index);
            }
            if (this.match("PRINT")) {
                long print_expr_index = this.parse_expr();
                return new StmtNode("print", "", print_expr_index);
            }
            String assign_name = this.expect("IDENT").text;
            this.expect("EQUAL");
            long assign_expr_index = this.parse_expr();
            return new StmtNode("assign", assign_name, assign_expr_index);
        }

        public long parse_expr() {
            return this.parse_add();
        }

        public long parse_add() {
            long left = this.parse_mul();
            while (true) {
                if (this.match("PLUS")) {
                    long right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "+", left, right));
                    continue;
                }
                if (this.match("MINUS")) {
                    long right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "-", left, right));
                    continue;
                }
                break;
            }
            return left;
        }

        public long parse_mul() {
            long left = this.parse_unary();
            while (true) {
                if (this.match("STAR")) {
                    long right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "*", left, right));
                    continue;
                }
                if (this.match("SLASH")) {
                    long right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "/", left, right));
                    continue;
                }
                break;
            }
            return left;
        }

        public long parse_unary() {
            if (this.match("MINUS")) {
                long child = this.parse_unary();
                return this.add_expr(new ExprNode("neg", 0L, "", "", child, (-1L)));
            }
            return this.parse_primary();
        }

        public long parse_primary() {
            if (this.match("NUMBER")) {
                Token token_num = ((Token)(this.tokens.get((int)(((((this.pos - 1L)) < 0L) ? (((long)(this.tokens.size())) + ((this.pos - 1L))) : ((this.pos - 1L)))))));
                return this.add_expr(new ExprNode("lit", PyRuntime.__pytra_int(token_num.text), "", "", (-1L), (-1L)));
            }
            if (this.match("IDENT")) {
                Token token_ident = ((Token)(this.tokens.get((int)(((((this.pos - 1L)) < 0L) ? (((long)(this.tokens.size())) + ((this.pos - 1L))) : ((this.pos - 1L)))))));
                return this.add_expr(new ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L)));
            }
            if (this.match("LPAREN")) {
                long expr_index = this.parse_expr();
                this.expect("RPAREN");
                return expr_index;
            }
            Token t = ((Token)(this.tokens.get((int)((((this.pos) < 0L) ? (((long)(this.tokens.size())) + (this.pos)) : (this.pos))))));
            throw new RuntimeException(__pytra_str(new RuntimeError(((("primary parse error at pos=" + String.valueOf(t.pos)) + " got=") + t.kind))));
            return 0L;
        }
    }

    public static java.util.ArrayList<Object> tokenize(java.util.ArrayList<Object> lines) {
        java.util.ArrayList<Object> tokens = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(lines));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            long line_index = __iter_i_1;
            String source = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            long i = 0L;
            long n = ((long)(source.length()));
            while ((i < n)) {
                String ch = String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))));
                if ((java.util.Objects.equals(ch, " "))) {
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "+"))) {
                    tokens.add(new Token("PLUS", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "-"))) {
                    tokens.add(new Token("MINUS", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "*"))) {
                    tokens.add(new Token("STAR", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "/"))) {
                    tokens.add(new Token("SLASH", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "("))) {
                    tokens.add(new Token("LPAREN", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, ")"))) {
                    tokens.add(new Token("RPAREN", ch, i));
                    i += 1L;
                    continue;
                }
                if ((java.util.Objects.equals(ch, "="))) {
                    tokens.add(new Token("EQUAL", ch, i));
                    i += 1L;
                    continue;
                }
                if (PyRuntime.__pytra_truthy(PyRuntime.__pytra_str_isdigit(ch))) {
                    long start = i;
                    while (((i < n) && PyRuntime.__pytra_str_isdigit(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))))))) {
                        i += 1L;
                    }
                    String text = PyRuntime.__pytra_str_slice(source, (((start) < 0L) ? (((long)(source.length())) + (start)) : (start)), (((i) < 0L) ? (((long)(source.length())) + (i)) : (i)));
                    tokens.add(new Token("NUMBER", text, start));
                    continue;
                }
                if ((PyRuntime.__pytra_str_isalpha(ch) || (java.util.Objects.equals(ch, "_")))) {
                    long start = i;
                    while (((i < n) && ((PyRuntime.__pytra_str_isalpha(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))))) || (java.util.Objects.equals(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i)))))), "_"))) || PyRuntime.__pytra_str_isdigit(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i)))))))))) {
                        i += 1L;
                    }
                    String text = PyRuntime.__pytra_str_slice(source, (((start) < 0L) ? (((long)(source.length())) + (start)) : (start)), (((i) < 0L) ? (((long)(source.length())) + (i)) : (i)));
                    if ((java.util.Objects.equals(text, "let"))) {
                        tokens.add(new Token("LET", text, start));
                    } else {
                        if ((java.util.Objects.equals(text, "print"))) {
                            tokens.add(new Token("PRINT", text, start));
                        } else {
                            tokens.add(new Token("IDENT", text, start));
                        }
                    }
                    continue;
                }
                throw new RuntimeException(__pytra_str(new RuntimeError(((((("tokenize error at line=" + String.valueOf(line_index)) + " pos=") + String.valueOf(i)) + " ch=") + ch))));
            }
            tokens.add(new Token("NEWLINE", "", n));
        }
        tokens.add(new Token("EOF", "", ((long)(lines.size()))));
        return tokens;
    }

    public static long eval_expr(long expr_index, java.util.ArrayList<Object> expr_nodes, java.util.HashMap<Object, Object> env) {
        ExprNode node = ((ExprNode)(expr_nodes.get((int)((((expr_index) < 0L) ? (((long)(expr_nodes.size())) + (expr_index)) : (expr_index))))));
        if ((java.util.Objects.equals(node.kind, "lit"))) {
            return node.value;
        }
        if ((java.util.Objects.equals(node.kind, "var"))) {
            if ((!(env.containsKey(node.name)))) {
                throw new RuntimeException(__pytra_str(new RuntimeError(("undefined variable: " + node.name))));
            }
            return ((Long)(env.get(node.name)));
        }
        if ((java.util.Objects.equals(node.kind, "neg"))) {
            return (-eval_expr(node.left, expr_nodes, env));
        }
        if ((java.util.Objects.equals(node.kind, "bin"))) {
            long lhs = eval_expr(node.left, expr_nodes, env);
            long rhs = eval_expr(node.right, expr_nodes, env);
            if ((java.util.Objects.equals(node.op, "+"))) {
                return (lhs + rhs);
            }
            if ((java.util.Objects.equals(node.op, "-"))) {
                return (lhs - rhs);
            }
            if ((java.util.Objects.equals(node.op, "*"))) {
                return (lhs * rhs);
            }
            if ((java.util.Objects.equals(node.op, "/"))) {
                if ((rhs == 0L)) {
                    throw new RuntimeException(__pytra_str(new RuntimeError("division by zero")));
                }
                return (lhs / rhs);
            }
            throw new RuntimeException(__pytra_str(new RuntimeError(("unknown operator: " + node.op))));
        }
        throw new RuntimeException(__pytra_str(new RuntimeError(("unknown node kind: " + node.kind))));
        return 0L;
    }

    public static long execute(java.util.ArrayList<Object> stmts, java.util.ArrayList<Object> expr_nodes, boolean trace) {
        java.util.HashMap<Object, Object> env = new java.util.HashMap<Object, Object>();
        long checksum = 0L;
        long printed = 0L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(stmts));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            StmtNode stmt = ((StmtNode)(__iter_0.get((int)(__iter_i_1))));
            if ((java.util.Objects.equals(stmt.kind, "let"))) {
                env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            if ((java.util.Objects.equals(stmt.kind, "assign"))) {
                if ((!(env.containsKey(stmt.name)))) {
                    throw new RuntimeException(__pytra_str(new RuntimeError(("assign to undefined variable: " + stmt.name))));
                }
                env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            long value = eval_expr(stmt.expr_index, expr_nodes, env);
            if (trace) {
                System.out.println(value);
            }
            long norm = (value % 1000000007L);
            if ((norm < 0L)) {
                norm += 1000000007L;
            }
            checksum = (((checksum * 131L) + norm) % 1000000007L);
            printed += 1L;
        }
        if (trace) {
            System.out.println(String.valueOf("printed:") + " " + String.valueOf(printed));
        }
        return checksum;
    }

    public static java.util.ArrayList<Object> build_benchmark_source(long var_count, long loops) {
        java.util.ArrayList<Object> lines = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        long __step_0 = 1L;
        for (long i = 0L; (__step_0 >= 0L) ? (i < var_count) : (i > var_count); i += __step_0) {
            lines.add(((("let v" + String.valueOf(i)) + " = ") + String.valueOf((i + 1L))));
        }
        long __step_1 = 1L;
        for (long i = 0L; (__step_1 >= 0L) ? (i < loops) : (i > loops); i += __step_1) {
            long x = (i % var_count);
            long y = ((i + 3L) % var_count);
            long c1 = ((i % 7L) + 1L);
            long c2 = ((i % 11L) + 2L);
            lines.add(((((((((("v" + String.valueOf(x)) + " = (v") + String.valueOf(x)) + " * ") + String.valueOf(c1)) + " + v") + String.valueOf(y)) + " + 10000) / ") + String.valueOf(c2)));
            if (((i % 97L) == 0L)) {
                lines.add(("print v" + String.valueOf(x)));
            }
        }
        lines.add("print (v0 + v1 + v2 + v3)");
        return lines;
    }

    public static void run_demo() {
        java.util.ArrayList<Object> demo_lines = new java.util.ArrayList<Object>(java.util.Arrays.asList());
        demo_lines.add("let a = 10");
        demo_lines.add("let b = 3");
        demo_lines.add("a = (a + b) * 2");
        demo_lines.add("print a");
        demo_lines.add("print a / b");
        java.util.ArrayList<Object> tokens = tokenize(demo_lines);
        Parser parser = new Parser(tokens);
        java.util.ArrayList<Object> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, true);
        System.out.println(String.valueOf("demo_checksum:") + " " + String.valueOf(checksum));
    }

    public static void run_benchmark() {
        java.util.ArrayList<Object> source_lines = build_benchmark_source(32L, 120000L);
        double start = (System.nanoTime() / 1000000000.0);
        java.util.ArrayList<Object> tokens = tokenize(source_lines);
        Parser parser = new Parser(tokens);
        java.util.ArrayList<Object> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, false);
        double elapsed = ((System.nanoTime() / 1000000000.0) - start);
        System.out.println(String.valueOf("token_count:") + " " + String.valueOf(((long)(tokens.size()))));
        System.out.println(String.valueOf("expr_count:") + " " + String.valueOf(PyRuntime.__pytra_len(parser.expr_nodes)));
        System.out.println(String.valueOf("stmt_count:") + " " + String.valueOf(((long)(stmts.size()))));
        System.out.println(String.valueOf("checksum:") + " " + String.valueOf(checksum));
        System.out.println(String.valueOf("elapsed_sec:") + " " + String.valueOf(elapsed));
    }

    public static void __pytra_main() {
        run_demo();
        run_benchmark();
    }

    public static void main(String[] args) {
        __pytra_main();
    }
}
