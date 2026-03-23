final class _18_mini_language_interpreter {
    private _18_mini_language_interpreter() {
    }


    public static class Token {
        public String kind;
        public String text;
        public long pos;
        public long number_value;
        public Token() {
        }

        public Token(String kind, String text, long pos, long number_value) {
            this.kind = kind;
            this.text = text;
            this.pos = pos;
            this.number_value = number_value;
        }
    }

    public static class ExprNode {
        public String kind;
        public long value;
        public String name;
        public String op;
        public long left;
        public long right;
        public long kind_tag;
        public long op_tag;
        public ExprNode() {
        }

        public ExprNode(String kind, long value, String name, String op, long left, long right, long kind_tag, long op_tag) {
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

    public static class StmtNode {
        public String kind;
        public String name;
        public long expr_index;
        public long kind_tag;
        public StmtNode() {
        }

        public StmtNode(String kind, String name, long expr_index, long kind_tag) {
            this.kind = kind;
            this.name = name;
            this.expr_index = expr_index;
            this.kind_tag = kind_tag;
        }
    }

    public static class Parser {
        public java.util.ArrayList<Token> tokens;
        public long pos;
        public java.util.ArrayList<ExprNode> expr_nodes;

        public java.util.ArrayList<ExprNode> new_expr_nodes() {
            return new java.util.ArrayList<ExprNode>();
        }

        public Parser(java.util.ArrayList<Token> tokens) {
            this.tokens = tokens;
            this.pos = 0L;
            this.expr_nodes = this.new_expr_nodes();
        }

        public Token current_token() {
            return ((Token)(this.tokens.get((int)((((this.pos) < 0L) ? (((long)(this.tokens.size())) + (this.pos)) : (this.pos))))));
        }

        public Token previous_token() {
            return ((Token)(this.tokens.get((int)((((this.pos - 1L) < 0L) ? (((long)(this.tokens.size())) + (this.pos - 1L)) : (this.pos - 1L))))));
        }

        public String peek_kind() {
            return this.current_token().kind;
        }

        public boolean match(String kind) {
            if ((java.util.Objects.equals(this.peek_kind(), kind))) {
                this.pos += 1L;
                return true;
            }
            return false;
        }

        public Token expect(String kind) {
            Token token = this.current_token();
            if ((!(java.util.Objects.equals(token.kind, kind)))) {
                throw new RuntimeException(PyRuntime.pyToString("parse error at pos=" + String.valueOf(token.pos) + ", expected=" + kind + ", got=" + token.kind));
            }
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
            return ((long)(this.expr_nodes.size())) - 1L;
        }

        public java.util.ArrayList<StmtNode> parse_program() {
            java.util.ArrayList<StmtNode> stmts = new java.util.ArrayList<StmtNode>();
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
                return new StmtNode("let", let_name, let_expr_index, 1L);
            }
            if (this.match("PRINT")) {
                long print_expr_index = this.parse_expr();
                return new StmtNode("print", "", print_expr_index, 3L);
            }
            String assign_name = this.expect("IDENT").text;
            this.expect("EQUAL");
            long assign_expr_index = this.parse_expr();
            return new StmtNode("assign", assign_name, assign_expr_index, 2L);
        }

        public long parse_expr() {
            return this.parse_add();
        }

        public long parse_add() {
            long left = this.parse_mul();
            while (true) {
                long right = 0L;
                if (this.match("PLUS")) {
                    right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "+", left, right, 3L, 1L));
                    continue;
                }
                if (this.match("MINUS")) {
                    right = this.parse_mul();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "-", left, right, 3L, 2L));
                    continue;
                }
                break;
            }
            return left;
        }

        public long parse_mul() {
            long left = this.parse_unary();
            while (true) {
                long right = 0L;
                if (this.match("STAR")) {
                    right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "*", left, right, 3L, 3L));
                    continue;
                }
                if (this.match("SLASH")) {
                    right = this.parse_unary();
                    left = this.add_expr(new ExprNode("bin", 0L, "", "/", left, right, 3L, 4L));
                    continue;
                }
                break;
            }
            return left;
        }

        public long parse_unary() {
            if (this.match("MINUS")) {
                long child = this.parse_unary();
                return this.add_expr(new ExprNode("neg", 0L, "", "", child, (-(1L)), 4L, 0L));
            }
            return this.parse_primary();
        }

        public long parse_primary() {
            if (this.match("NUMBER")) {
                Token token_num = this.previous_token();
                return this.add_expr(new ExprNode("lit", token_num.number_value, "", "", (-(1L)), (-(1L)), 1L, 0L));
            }
            if (this.match("IDENT")) {
                Token token_ident = this.previous_token();
                return this.add_expr(new ExprNode("var", 0L, token_ident.text, "", (-(1L)), (-(1L)), 2L, 0L));
            }
            if (this.match("LPAREN")) {
                long expr_index = this.parse_expr();
                this.expect("RPAREN");
                return expr_index;
            }
            Token t = this.current_token();
            throw new RuntimeException(PyRuntime.pyToString("primary parse error at pos=" + String.valueOf(t.pos) + " got=" + t.kind));
        }
    }

    public static java.util.ArrayList<Token> tokenize(java.util.ArrayList<String> lines) {
        java.util.HashMap<String, Long> single_char_token_tags = ((java.util.HashMap<String, Long>)(Object)(PyRuntime.__pytra_dict_of("+", 1L, "-", 2L, "*", 3L, "/", 4L, "(", 5L, ")", 6L, "=", 7L)));
        java.util.ArrayList<String> single_char_token_kinds = new java.util.ArrayList<String>(java.util.Arrays.asList("PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"));
        java.util.ArrayList<Token> tokens = new java.util.ArrayList<Token>();
        long __enum_idx_1 = 0L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(lines));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            String source = String.valueOf(__iter_0.get((int)(__iter_i_1)));
            long line_index = __enum_idx_1;
            long i = 0L;
            long n = ((long)(source.length()));
            while (((i) < (n))) {
                String ch = String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))));
                if ((java.util.Objects.equals(ch, " "))) {
                    i += 1L;
                    continue;
                }
                long single_tag = ((Long)(PyRuntime.__pytra_dict_get_default(single_char_token_tags, ch, 0L)));
                if (((single_tag) > (0L))) {
                    tokens.add(new Token(String.valueOf(single_char_token_kinds.get((int)((((single_tag - 1L) < 0L) ? (((long)(single_char_token_kinds.size())) + (single_tag - 1L)) : (single_tag - 1L))))), ch, i, 0L));
                    i += 1L;
                    continue;
                }
                long start = 0L;
                String text = "";
                if (PyRuntime.__pytra_str_isdigit(ch)) {
                    start = i;
                    while ((((i) < (n)) && PyRuntime.__pytra_str_isdigit(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))))))) {
                        i += 1L;
                    }
                    text = PyRuntime.__pytra_str_slice(source, (((start) < 0L) ? (((long)(source.length())) + (start)) : (start)), (((i) < 0L) ? (((long)(source.length())) + (i)) : (i)));
                    tokens.add(new Token("NUMBER", text, start, PyRuntime.__pytra_int(text)));
                    continue;
                }
                if ((PyRuntime.__pytra_str_isalpha(ch) || (java.util.Objects.equals(ch, "_")))) {
                    start = i;
                    while ((((i) < (n)) && ((PyRuntime.__pytra_str_isalpha(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i))))))) || (java.util.Objects.equals(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i)))))), "_"))) || PyRuntime.__pytra_str_isdigit(String.valueOf(String.valueOf(source.charAt((int)((((i) < 0L) ? (((long)(source.length())) + (i)) : (i)))))))))) {
                        i += 1L;
                    }
                    text = PyRuntime.__pytra_str_slice(source, (((start) < 0L) ? (((long)(source.length())) + (start)) : (start)), (((i) < 0L) ? (((long)(source.length())) + (i)) : (i)));
                    if ((java.util.Objects.equals(text, "let"))) {
                        tokens.add(new Token("LET", text, start, 0L));
                    } else {
                        if ((java.util.Objects.equals(text, "print"))) {
                            tokens.add(new Token("PRINT", text, start, 0L));
                        } else {
                            tokens.add(new Token("IDENT", text, start, 0L));
                        }
                    }
                    continue;
                }
                throw new RuntimeException(PyRuntime.pyToString("tokenize error at line=" + String.valueOf(line_index) + " pos=" + String.valueOf(i) + " ch=" + ch));
            }
            tokens.add(new Token("NEWLINE", "", n, 0L));
            __enum_idx_1 += 1L;
        }
        tokens.add(new Token("EOF", "", ((long)(lines.size())), 0L));
        return tokens;
    }

    public static long eval_expr(long expr_index, java.util.ArrayList<ExprNode> expr_nodes, java.util.HashMap<String, Long> env) {
        ExprNode node = ((ExprNode)(expr_nodes.get((int)((((expr_index) < 0L) ? (((long)(expr_nodes.size())) + (expr_index)) : (expr_index))))));
        if (((node.kind_tag) == (1L))) {
            return node.value;
        }
        if (((node.kind_tag) == (2L))) {
            if ((!(env.containsKey(node.name)))) {
                throw new RuntimeException(PyRuntime.pyToString("undefined variable: " + node.name));
            }
            return ((Long)(env.get(node.name)));
        }
        if (((node.kind_tag) == (4L))) {
            return (-(eval_expr(node.left, expr_nodes, env)));
        }
        if (((node.kind_tag) == (3L))) {
            long lhs = eval_expr(node.left, expr_nodes, env);
            long rhs = eval_expr(node.right, expr_nodes, env);
            if (((node.op_tag) == (1L))) {
                return lhs + rhs;
            }
            if (((node.op_tag) == (2L))) {
                return lhs - rhs;
            }
            if (((node.op_tag) == (3L))) {
                return lhs * rhs;
            }
            if (((node.op_tag) == (4L))) {
                if (((rhs) == (0L))) {
                    throw new RuntimeException(PyRuntime.pyToString("division by zero"));
                }
                return lhs / rhs;
            }
            throw new RuntimeException(PyRuntime.pyToString("unknown operator: " + node.op));
        }
        throw new RuntimeException(PyRuntime.pyToString("unknown node kind: " + node.kind));
    }

    public static long execute(java.util.ArrayList<StmtNode> stmts, java.util.ArrayList<ExprNode> expr_nodes, boolean trace) {
        java.util.HashMap<String, Long> env = new java.util.HashMap<String, Long>();
        long checksum = 0L;
        long printed = 0L;
        java.util.ArrayList<Object> __iter_0 = ((java.util.ArrayList<Object>)(Object)(stmts));
        for (long __iter_i_1 = 0L; __iter_i_1 < ((long)(__iter_0.size())); __iter_i_1 += 1L) {
            StmtNode stmt = ((StmtNode)(__iter_0.get((int)(__iter_i_1))));
            if (((stmt.kind_tag) == (1L))) {
                env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            if (((stmt.kind_tag) == (2L))) {
                if ((!(env.containsKey(stmt.name)))) {
                    throw new RuntimeException(PyRuntime.pyToString("assign to undefined variable: " + stmt.name));
                }
                env.put(stmt.name, eval_expr(stmt.expr_index, expr_nodes, env));
                continue;
            }
            long value = eval_expr(stmt.expr_index, expr_nodes, env);
            if (trace) {
                System.out.println(value);
            }
            long norm = value % 1000000007L;
            if (((norm) < (0L))) {
                norm += 1000000007L;
            }
            checksum = (checksum * 131L + norm) % 1000000007L;
            printed += 1L;
        }
        if (trace) {
            System.out.println(String.valueOf("printed:") + " " + String.valueOf(printed));
        }
        return checksum;
    }

    public static java.util.ArrayList<String> build_benchmark_source(long var_count, long loops) {
        java.util.ArrayList<String> lines = new java.util.ArrayList<String>();
        long i = 0L;
        for (i = 0L; i < var_count; i += 1L) {
            lines.add("let v" + String.valueOf(i) + " = " + String.valueOf(i + 1L));
        }
        for (i = 0L; i < loops; i += 1L) {
            long x = i % var_count;
            long y = (i + 3L) % var_count;
            long c1 = i % 7L + 1L;
            long c2 = i % 11L + 2L;
            lines.add("v" + String.valueOf(x) + " = (v" + String.valueOf(x) + " * " + String.valueOf(c1) + " + v" + String.valueOf(y) + " + 10000) / " + String.valueOf(c2));
            if (((i % 97L) == (0L))) {
                lines.add("print v" + String.valueOf(x));
            }
        }
        lines.add("print (v0 + v1 + v2 + v3)");
        return lines;
    }

    public static void run_demo() {
        java.util.ArrayList<String> demo_lines = new java.util.ArrayList<String>();
        demo_lines.add("let a = 10");
        demo_lines.add("let b = 3");
        demo_lines.add("a = (a + b) * 2");
        demo_lines.add("print a");
        demo_lines.add("print a / b");
        java.util.ArrayList<Token> tokens = tokenize(demo_lines);
        Parser parser = new Parser(tokens);
        java.util.ArrayList<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, true);
        System.out.println(String.valueOf("demo_checksum:") + " " + String.valueOf(checksum));
    }

    public static void run_benchmark() {
        String out_path = "sample/out/18_mini_language_interpreter.txt";
        java.util.ArrayList<String> source_lines = build_benchmark_source(32L, 120000L);
        double start = time.perf_counter();
        java.util.ArrayList<Token> tokens = tokenize(source_lines);
        Parser parser = new Parser(tokens);
        java.util.ArrayList<StmtNode> stmts = parser.parse_program();
        long checksum = execute(stmts, parser.expr_nodes, false);
        double elapsed = time.perf_counter() - start;
        String result = "token_count:" + String.valueOf(((long)(tokens.size()))) + "\nexpr_count:" + String.valueOf(PyRuntime.__pytra_len(parser.expr_nodes)) + "\nstmt_count:" + String.valueOf(((long)(stmts.size()))) + "\nchecksum:" + String.valueOf(checksum) + "\n";
        pathlib.Path p = new pathlib.Path(out_path);
        p.write_text(result, "utf-8");
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

    public static void _case_main() {
        __pytra_main();
    }
}
