import Foundation


func __pytra_is_Token(_ v: Any?) -> Bool {
    return v is Token
}

func __pytra_is_ExprNode(_ v: Any?) -> Bool {
    return v is ExprNode
}

func __pytra_is_StmtNode(_ v: Any?) -> Bool {
    return v is StmtNode
}

func __pytra_is_Parser(_ v: Any?) -> Bool {
    return v is Parser
}

class Token {
    var kind: String = ""
    var text: String = ""
    var pos: Int64 = 0
    var number_value: Int64 = 0

    init() {
    }
}

class ExprNode {
    var kind: String = ""
    var value: Int64 = 0
    var name: String = ""
    var op: String = ""
    var left: Int64 = 0
    var right: Int64 = 0
    var kind_tag: Int64 = 0
    var op_tag: Int64 = 0

    init() {
    }
}

class StmtNode {
    var kind: String = ""
    var name: String = ""
    var expr_index: Int64 = 0
    var kind_tag: Int64 = 0

    init() {
    }
}

class Parser {
    var tokens: [Any] = []
    var pos: Int64 = 0
    var expr_nodes: [Any] = []

    func new_expr_nodes() -> [Any] {
        return __pytra_as_list([])
    }

    init(tokens: [Any]) {
        self.tokens = tokens
        self.pos = Int64(0)
        self.expr_nodes = self.new_expr_nodes()
    }

    func current_token() -> Token {
        return ((__pytra_getIndex(self.tokens, self.pos) as? Token) ?? Token() as? Token) ?? Token()
    }

    func previous_token() -> Token {
        return ((__pytra_getIndex(self.tokens, (self.pos - Int64(1))) as? Token) ?? Token() as? Token) ?? Token()
    }

    func peek_kind() -> String {
        return __pytra_str(self.current_token().kind)
    }

    func match(kind: String) -> Bool {
        if (__pytra_str(self.peek_kind()) == __pytra_str(kind)) {
            self.pos += Int64(1)
            return true
        }
        return false
    }

    func expect(kind: String) -> Token {
        var token: Token = (self.current_token() as? Token) ?? Token()
        if (__pytra_str(token.kind) != __pytra_str(kind)) {
            fatalError("pytra raise")
        }
        self.pos += Int64(1)
        return token
    }

    func skip_newlines() {
        while self.match("NEWLINE") {
            _ = 0
        }
    }

    func add_expr(node: ExprNode) -> Int64 {
        self.expr_nodes = __pytra_as_list(self.expr_nodes); self.expr_nodes.append(node)
        return (__pytra_len(self.expr_nodes) - Int64(1))
    }

    func parse_program() -> [Any] {
        var stmts: [Any] = __pytra_as_list([])
        self.skip_newlines()
        while (__pytra_str(self.peek_kind()) != __pytra_str("EOF")) {
            var stmt: StmtNode = (self.parse_stmt() as? StmtNode) ?? StmtNode()
            stmts.append(stmt)
            self.skip_newlines()
        }
        return stmts
    }

    func parse_stmt() -> StmtNode {
        if self.match("LET") {
            var let_name: String = __pytra_str(self.expect("IDENT").text)
            self.expect("EQUAL")
            var let_expr_index: Int64 = __pytra_int(self.parse_expr())
            return (StmtNode("let", let_name, let_expr_index, Int64(1)) as? StmtNode) ?? StmtNode()
        }
        if self.match("PRINT") {
            var print_expr_index: Int64 = __pytra_int(self.parse_expr())
            return (StmtNode("print", "", print_expr_index, Int64(3)) as? StmtNode) ?? StmtNode()
        }
        var assign_name: String = __pytra_str(self.expect("IDENT").text)
        self.expect("EQUAL")
        var assign_expr_index: Int64 = __pytra_int(self.parse_expr())
        return (StmtNode("assign", assign_name, assign_expr_index, Int64(2)) as? StmtNode) ?? StmtNode()
    }

    func parse_expr() -> Int64 {
        return __pytra_int(self.parse_add())
    }

    func parse_add() -> Int64 {
        var left: Int64 = __pytra_int(self.parse_mul())
        while true {
            if self.match("PLUS") {
                var right: Int64 = __pytra_int(self.parse_mul())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "+", left, right, Int64(3), Int64(1))))
                continue
            }
            if self.match("MINUS") {
                var right: Int64 = __pytra_int(self.parse_mul())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "-", left, right, Int64(3), Int64(2))))
                continue
            }
            break
        }
        return left
    }

    func parse_mul() -> Int64 {
        var left: Int64 = __pytra_int(self.parse_unary())
        while true {
            if self.match("STAR") {
                var right: Int64 = __pytra_int(self.parse_unary())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "*", left, right, Int64(3), Int64(3))))
                continue
            }
            if self.match("SLASH") {
                var right: Int64 = __pytra_int(self.parse_unary())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "/", left, right, Int64(3), Int64(4))))
                continue
            }
            break
        }
        return left
    }

    func parse_unary() -> Int64 {
        if self.match("MINUS") {
            var child: Int64 = __pytra_int(self.parse_unary())
            return __pytra_int(self.add_expr(ExprNode("neg", Int64(0), "", "", child, (-Int64(1)), Int64(4), Int64(0))))
        }
        return __pytra_int(self.parse_primary())
    }

    func parse_primary() -> Int64 {
        if self.match("NUMBER") {
            var token_num: Token = (self.previous_token() as? Token) ?? Token()
            return __pytra_int(self.add_expr(ExprNode("lit", token_num.number_value, "", "", (-Int64(1)), (-Int64(1)), Int64(1), Int64(0))))
        }
        if self.match("IDENT") {
            var token_ident: Token = (self.previous_token() as? Token) ?? Token()
            return __pytra_int(self.add_expr(ExprNode("var", Int64(0), token_ident.text, "", (-Int64(1)), (-Int64(1)), Int64(2), Int64(0))))
        }
        if self.match("LPAREN") {
            var expr_index: Int64 = __pytra_int(self.parse_expr())
            self.expect("RPAREN")
            return expr_index
        }
        var t: Token = (self.current_token() as? Token) ?? Token()
        fatalError("pytra raise")
        return 0
    }
}

func tokenize(lines: [Any]) -> [Any] {
    var single_char_token_tags: [AnyHashable: Any] = __pytra_as_dict([:])
    var single_char_token_kinds: [Any] = __pytra_as_list(["PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"])
    var tokens: [Any] = __pytra_as_list([])
    let __iter_0 = __pytra_as_list(enumerate(lines))
    var __i_1: Int64 = 0
    while __i_1 < Int64(__iter_0.count) {
        let __tuple_2 = __pytra_as_list(__iter_0[Int(__i_1)])
        let line_index = __tuple_2[Int(0)]
        let source = __tuple_2[Int(1)]
        var i: Int64 = Int64(0)
        var n: Int64 = __pytra_len(source)
        while (__pytra_int(i) < __pytra_int(n)) {
            var ch: String = __pytra_str(__pytra_getIndex(source, i))
            if (__pytra_str(ch) == __pytra_str(" ")) {
                i += Int64(1)
                continue
            }
            var single_tag: Int64 = __pytra_int(single_char_token_tags.get(ch, Int64(0)))
            if (__pytra_int(single_tag) > __pytra_int(Int64(0))) {
                tokens.append(Token(__pytra_str(__pytra_getIndex(single_char_token_kinds, (single_tag - Int64(1)))), ch, i, Int64(0)))
                i += Int64(1)
                continue
            }
            if __pytra_truthy(__pytra_isdigit(ch)) {
                var start: Int64 = i
                while ((__pytra_int(i) < __pytra_int(n)) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_getIndex(source, i))))) {
                    i += Int64(1)
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                tokens.append(Token("NUMBER", text, start, __pytra_int(text)))
                continue
            }
            if (__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_"))) {
                var start: Int64 = i
                while ((__pytra_int(i) < __pytra_int(n)) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_getIndex(source, i)))) || (__pytra_str(__pytra_getIndex(source, i)) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_getIndex(source, i)))))) {
                    i += Int64(1)
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                if (__pytra_str(text) == __pytra_str("let")) {
                    tokens.append(Token("LET", text, start, Int64(0)))
                } else {
                    if (__pytra_str(text) == __pytra_str("print")) {
                        tokens.append(Token("PRINT", text, start, Int64(0)))
                    } else {
                        tokens.append(Token("IDENT", text, start, Int64(0)))
                    }
                }
                continue
            }
            fatalError("pytra raise")
        }
        tokens.append(Token("NEWLINE", "", n, Int64(0)))
        __i_1 += 1
    }
    tokens.append(Token("EOF", "", __pytra_len(lines), Int64(0)))
    return tokens
}

func eval_expr(expr_index: Int64, expr_nodes: [Any], env: [AnyHashable: Any]) -> Int64 {
    var node: ExprNode = ((__pytra_getIndex(expr_nodes, expr_index) as? ExprNode) ?? ExprNode() as? ExprNode) ?? ExprNode()
    if (__pytra_int(node.kind_tag) == __pytra_int(Int64(1))) {
        return __pytra_int(node.value)
    }
    if (__pytra_int(node.kind_tag) == __pytra_int(Int64(2))) {
        if (!(__pytra_contains(env, node.name))) {
            fatalError("pytra raise")
        }
        return __pytra_int(__pytra_getIndex(env, node.name))
    }
    if (__pytra_int(node.kind_tag) == __pytra_int(Int64(4))) {
        return __pytra_int(-eval_expr(node.left, expr_nodes, env))
    }
    if (__pytra_int(node.kind_tag) == __pytra_int(Int64(3))) {
        var lhs: Int64 = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Int64 = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if (__pytra_int(node.op_tag) == __pytra_int(Int64(1))) {
            return (lhs + rhs)
        }
        if (__pytra_int(node.op_tag) == __pytra_int(Int64(2))) {
            return (lhs - rhs)
        }
        if (__pytra_int(node.op_tag) == __pytra_int(Int64(3))) {
            return (lhs * rhs)
        }
        if (__pytra_int(node.op_tag) == __pytra_int(Int64(4))) {
            if (__pytra_int(rhs) == __pytra_int(Int64(0))) {
                fatalError("pytra raise")
            }
            return (lhs / rhs)
        }
        fatalError("pytra raise")
    }
    fatalError("pytra raise")
    return 0
}

func execute(stmts: [Any], expr_nodes: [Any], trace: Bool) -> Int64 {
    var env: [AnyHashable: Any] = __pytra_as_dict([:])
    var checksum: Int64 = Int64(0)
    var printed: Int64 = Int64(0)
    let __iter_0 = __pytra_as_list(stmts)
    var __i_1: Int64 = 0
    while __i_1 < Int64(__iter_0.count) {
        let stmt = __iter_0[Int(__i_1)]
        if (__pytra_int(stmt.kind_tag) == __pytra_int(Int64(1))) {
            __pytra_setIndex(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            __i_1 += 1
            continue
        }
        if (__pytra_int(stmt.kind_tag) == __pytra_int(Int64(2))) {
            if (!(__pytra_contains(env, stmt.name))) {
                fatalError("pytra raise")
            }
            __pytra_setIndex(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            __i_1 += 1
            continue
        }
        var value: Int64 = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
        if trace {
            __pytra_print(value)
        }
        var norm: Int64 = (value % Int64(1000000007))
        if (__pytra_int(norm) < __pytra_int(Int64(0))) {
            norm += Int64(1000000007)
        }
        checksum = (((checksum * Int64(131)) + norm) % Int64(1000000007))
        printed += Int64(1)
        __i_1 += 1
    }
    if trace {
        __pytra_print("printed:", printed)
    }
    return checksum
}

func build_benchmark_source(var_count: Int64, loops: Int64) -> [Any] {
    var lines: [Any] = __pytra_as_list([])
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(var_count)) {
        lines.append((__pytra_str(__pytra_str(__pytra_str("let v") + __pytra_str(i)) + __pytra_str(" = ")) + __pytra_str(i + Int64(1))))
        i += 1
    }
    var i = __pytra_int(Int64(0))
    while (i < __pytra_int(loops)) {
        var x: Int64 = (i % var_count)
        var y: Int64 = ((i + Int64(3)) % var_count)
        var c1: Int64 = ((i % Int64(7)) + Int64(1))
        var c2: Int64 = ((i % Int64(11)) + Int64(2))
        lines.append((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str(__pytra_str("v") + __pytra_str(x)) + __pytra_str(" = (v"))) + __pytra_str(x))) + __pytra_str(" * "))) + __pytra_str(c1))) + __pytra_str(" + v"))) + __pytra_str(y))) + __pytra_str(" + 10000) / ") + __pytra_str(c2)))
        if (__pytra_int(i % Int64(97)) == __pytra_int(Int64(0))) {
            lines.append((__pytra_str("print v") + __pytra_str(x)))
        }
        i += 1
    }
    lines.append("print (v0 + v1 + v2 + v3)")
    return lines
}

func run_demo() {
    var demo_lines: [Any] = __pytra_as_list([])
    demo_lines.append("let a = 10")
    demo_lines.append("let b = 3")
    demo_lines.append("a = (a + b) * 2")
    demo_lines.append("print a")
    demo_lines.append("print a / b")
    var tokens: [Any] = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = (Parser(tokens) as? Parser) ?? Parser()
    var stmts: [Any] = __pytra_as_list(parser.parse_program())
    var checksum: Int64 = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

func run_benchmark() {
    var source_lines: [Any] = __pytra_as_list(build_benchmark_source(Int64(32), Int64(120000)))
    var start: Double = __pytra_perf_counter()
    var tokens: [Any] = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = (Parser(tokens) as? Parser) ?? Parser()
    var stmts: [Any] = __pytra_as_list(parser.parse_program())
    var checksum: Int64 = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("token_count:", __pytra_len(tokens))
    __pytra_print("expr_count:", __pytra_len(parser.expr_nodes))
    __pytra_print("stmt_count:", __pytra_len(stmts))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

func __pytra_main() {
    run_demo()
    run_benchmark()
}

@main
struct Main {
    static func main() {
        main()
    }
}
