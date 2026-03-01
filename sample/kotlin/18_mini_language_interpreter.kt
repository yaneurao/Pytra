import kotlin.math.*


fun __pytra_is_Token(v: Any?): Boolean {
    return v is Token
}

fun __pytra_as_Token(v: Any?): Token {
    return if (v is Token) v else Token()
}

fun __pytra_is_ExprNode(v: Any?): Boolean {
    return v is ExprNode
}

fun __pytra_as_ExprNode(v: Any?): ExprNode {
    return if (v is ExprNode) v else ExprNode()
}

fun __pytra_is_StmtNode(v: Any?): Boolean {
    return v is StmtNode
}

fun __pytra_as_StmtNode(v: Any?): StmtNode {
    return if (v is StmtNode) v else StmtNode()
}

fun __pytra_is_Parser(v: Any?): Boolean {
    return v is Parser
}

fun __pytra_as_Parser(v: Any?): Parser {
    return if (v is Parser) v else Parser()
}

open class Token() {
    var kind: String = ""
    var text: String = ""
    var pos: Long = 0L
    var number_value: Long = 0L

    constructor(kind: String, text: String, pos: Long, number_value: Long) : this() {
        this.kind = kind
        this.text = text
        this.pos = pos
        this.number_value = number_value
    }
}

open class ExprNode() {
    var kind: String = ""
    var value: Long = 0L
    var name: String = ""
    var op: String = ""
    var left: Long = 0L
    var right: Long = 0L
    var kind_tag: Long = 0L
    var op_tag: Long = 0L

    constructor(kind: String, value: Long, name: String, op: String, left: Long, right: Long, kind_tag: Long, op_tag: Long) : this() {
        this.kind = kind
        this.value = value
        this.name = name
        this.op = op
        this.left = left
        this.right = right
        this.kind_tag = kind_tag
        this.op_tag = op_tag
    }
}

open class StmtNode() {
    var kind: String = ""
    var name: String = ""
    var expr_index: Long = 0L
    var kind_tag: Long = 0L

    constructor(kind: String, name: String, expr_index: Long, kind_tag: Long) : this() {
        this.kind = kind
        this.name = name
        this.expr_index = expr_index
        this.kind_tag = kind_tag
    }
}

open class Parser() {
    var tokens: MutableList<Any?> = mutableListOf()
    var pos: Long = 0L
    var expr_nodes: MutableList<Any?> = mutableListOf()

    open fun new_expr_nodes(): MutableList<Any?> {
        return __pytra_as_list(mutableListOf<Any?>())
    }

    constructor(tokens: MutableList<Any?>) : this() {
        this.tokens = tokens
        this.pos = 0L
        this.expr_nodes = this.new_expr_nodes()
    }

    open fun current_token(): Token {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
    }

    open fun previous_token(): Token {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, (this.pos - 1L))))
    }

    open fun peek_kind(): String {
        return __pytra_str(this.current_token().kind)
    }

    open fun match(kind: String): Boolean {
        if ((__pytra_str(this.peek_kind()) == __pytra_str(kind))) {
            this.pos += 1L
            return true
        }
        return false
    }

    open fun expect(kind: String): Token {
        var token: Token = __pytra_as_Token(this.current_token())
        if ((__pytra_str(token.kind) != __pytra_str(kind))) {
            throw RuntimeException(__pytra_str(((__pytra_str(__pytra_str(__pytra_str(__pytra_str("parse error at pos=") + __pytra_str(token.pos)) + __pytra_str(", expected=")) + __pytra_str(kind)) + __pytra_str(", got=")) + token.kind)))
        }
        this.pos += 1L
        return token
    }

    open fun skip_newlines() {
        while (this.match("NEWLINE")) {
            run { }
        }
    }

    open fun add_expr(node: ExprNode): Long {
        this.expr_nodes = __pytra_as_list(this.expr_nodes); this.expr_nodes.add(node)
        return (__pytra_len(this.expr_nodes) - 1L)
    }

    open fun parse_program(): MutableList<Any?> {
        var stmts: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        this.skip_newlines()
        while ((__pytra_str(this.peek_kind()) != __pytra_str("EOF"))) {
            var stmt: StmtNode = __pytra_as_StmtNode(this.parse_stmt())
            stmts.add(stmt)
            this.skip_newlines()
        }
        return stmts
    }

    open fun parse_stmt(): StmtNode {
        if (this.match("LET")) {
            var let_name: String = __pytra_str(this.expect("IDENT").text)
            this.expect("EQUAL")
            var let_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(StmtNode("let", let_name, let_expr_index, 1L))
        }
        if (this.match("PRINT")) {
            var print_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(StmtNode("print", "", print_expr_index, 3L))
        }
        var assign_name: String = __pytra_str(this.expect("IDENT").text)
        this.expect("EQUAL")
        var assign_expr_index: Long = __pytra_int(this.parse_expr())
        return __pytra_as_StmtNode(StmtNode("assign", assign_name, assign_expr_index, 2L))
    }

    open fun parse_expr(): Long {
        return __pytra_int(this.parse_add())
    }

    open fun parse_add(): Long {
        var left: Long = __pytra_int(this.parse_mul())
        while (true) {
            if (this.match("PLUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "+", left, right, 3L, 1L)))
                continue
            }
            if (this.match("MINUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "-", left, right, 3L, 2L)))
                continue
            }
            break
        }
        return left
    }

    open fun parse_mul(): Long {
        var left: Long = __pytra_int(this.parse_unary())
        while (true) {
            if (this.match("STAR")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "*", left, right, 3L, 3L)))
                continue
            }
            if (this.match("SLASH")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "/", left, right, 3L, 4L)))
                continue
            }
            break
        }
        return left
    }

    open fun parse_unary(): Long {
        if (this.match("MINUS")) {
            var child: Long = __pytra_int(this.parse_unary())
            return __pytra_int(this.add_expr(ExprNode("neg", 0L, "", "", child, (-1L), 4L, 0L)))
        }
        return __pytra_int(this.parse_primary())
    }

    open fun parse_primary(): Long {
        if (this.match("NUMBER")) {
            var token_num: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(ExprNode("lit", token_num.number_value, "", "", (-1L), (-1L), 1L, 0L)))
        }
        if (this.match("IDENT")) {
            var token_ident: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L), 2L, 0L)))
        }
        if (this.match("LPAREN")) {
            var expr_index: Long = __pytra_int(this.parse_expr())
            this.expect("RPAREN")
            return expr_index
        }
        var t: Token = __pytra_as_Token(this.current_token())
        throw RuntimeException(__pytra_str(((__pytra_str(__pytra_str("primary parse error at pos=") + __pytra_str(t.pos)) + __pytra_str(" got=")) + t.kind)))
        return 0L
    }
}

fun tokenize(lines: MutableList<Any?>): MutableList<Any?> {
    var single_char_token_tags: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf(Pair("+", 1L), Pair("-", 2L), Pair("*", 3L), Pair("/", 4L), Pair("(", 5L), Pair(")", 6L), Pair("=", 7L)))
    var single_char_token_kinds: MutableList<Any?> = __pytra_as_list(mutableListOf("PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"))
    var tokens: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val __it_2 = __iter_0[__i_1.toInt()]
        val __tuple_3 = __pytra_as_list(__it_2)
        var line_index: Long = __pytra_int(__tuple_3[0])
        var source: String = __pytra_str(__tuple_3[1])
        var i: Long = 0L
        var n: Long = __pytra_len(source)
        while ((__pytra_int(i) < __pytra_int(n))) {
            var ch: String = __pytra_str(__pytra_get_index(source, i))
            if ((__pytra_str(ch) == __pytra_str(" "))) {
                i += 1L
                continue
            }
            var single_tag: Long = __pytra_int(single_char_token_tags.get(ch) ?: 0L)
            if ((__pytra_int(single_tag) > __pytra_int(0L))) {
                tokens.add(Token(__pytra_str(__pytra_get_index(single_char_token_kinds, (single_tag - 1L))), ch, i, 0L))
                i += 1L
                continue
            }
            if (__pytra_truthy(__pytra_isdigit(ch))) {
                var start: Long = i
                while (((__pytra_int(i) < __pytra_int(n)) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i)))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                tokens.add(Token("NUMBER", text, start, __pytra_int(text)))
                continue
            }
            if ((__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_")))) {
                var start: Long = i
                while (((__pytra_int(i) < __pytra_int(n)) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_get_index(source, i)))) || (__pytra_str(__pytra_get_index(source, i)) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i))))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                if ((__pytra_str(text) == __pytra_str("let"))) {
                    tokens.add(Token("LET", text, start, 0L))
                } else {
                    if ((__pytra_str(text) == __pytra_str("print"))) {
                        tokens.add(Token("PRINT", text, start, 0L))
                    } else {
                        tokens.add(Token("IDENT", text, start, 0L))
                    }
                }
                continue
            }
            throw RuntimeException(__pytra_str((__pytra_str(__pytra_str(__pytra_str(__pytra_str(__pytra_str("tokenize error at line=") + __pytra_str(line_index)) + __pytra_str(" pos=")) + __pytra_str(i)) + __pytra_str(" ch=")) + __pytra_str(ch))))
        }
        tokens.add(Token("NEWLINE", "", n, 0L))
        __i_1 += 1L
    }
    tokens.add(Token("EOF", "", __pytra_len(lines), 0L))
    return tokens
}

fun eval_expr(expr_index: Long, expr_nodes: MutableList<Any?>, env: MutableMap<Any, Any?>): Long {
    var node: ExprNode = __pytra_as_ExprNode(__pytra_as_ExprNode(__pytra_get_index(expr_nodes, expr_index)))
    if ((__pytra_int(node.kind_tag) == __pytra_int(1L))) {
        return __pytra_int(node.value)
    }
    if ((__pytra_int(node.kind_tag) == __pytra_int(2L))) {
        if ((!(__pytra_contains(env, node.name)))) {
            throw RuntimeException(__pytra_str(("undefined variable: " + node.name)))
        }
        return __pytra_int(__pytra_get_index(env, node.name))
    }
    if ((__pytra_int(node.kind_tag) == __pytra_int(4L))) {
        return __pytra_int(-eval_expr(node.left, expr_nodes, env))
    }
    if ((__pytra_int(node.kind_tag) == __pytra_int(3L))) {
        var lhs: Long = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Long = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if ((__pytra_int(node.op_tag) == __pytra_int(1L))) {
            return (lhs + rhs)
        }
        if ((__pytra_int(node.op_tag) == __pytra_int(2L))) {
            return (lhs - rhs)
        }
        if ((__pytra_int(node.op_tag) == __pytra_int(3L))) {
            return (lhs * rhs)
        }
        if ((__pytra_int(node.op_tag) == __pytra_int(4L))) {
            if ((__pytra_int(rhs) == __pytra_int(0L))) {
                throw RuntimeException(__pytra_str("division by zero"))
            }
            return (lhs / rhs)
        }
        throw RuntimeException(__pytra_str(("unknown operator: " + node.op)))
    }
    throw RuntimeException(__pytra_str(("unknown node kind: " + node.kind)))
    return 0L
}

fun execute(stmts: MutableList<Any?>, expr_nodes: MutableList<Any?>, trace: Boolean): Long {
    var env: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf<Any, Any?>())
    var checksum: Long = 0L
    var printed: Long = 0L
    val __iter_0 = __pytra_as_list(stmts)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val stmt: StmtNode = __pytra_as_StmtNode(__iter_0[__i_1.toInt()])
        if ((__pytra_int(stmt.kind_tag) == __pytra_int(1L))) {
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            __i_1 += 1L
            continue
        }
        if ((__pytra_int(stmt.kind_tag) == __pytra_int(2L))) {
            if ((!(__pytra_contains(env, stmt.name)))) {
                throw RuntimeException(__pytra_str(("assign to undefined variable: " + stmt.name)))
            }
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            __i_1 += 1L
            continue
        }
        var value: Long = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
        if (trace) {
            __pytra_print(value)
        }
        var norm: Long = (value % 1000000007L)
        if ((__pytra_int(norm) < __pytra_int(0L))) {
            norm += 1000000007L
        }
        checksum = (((checksum * 131L) + norm) % 1000000007L)
        printed += 1L
        __i_1 += 1L
    }
    if (trace) {
        __pytra_print("printed:", printed)
    }
    return checksum
}

fun build_benchmark_source(var_count: Long, loops: Long): MutableList<Any?> {
    var lines: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    var i = __pytra_int(0L)
    while (i < __pytra_int(var_count)) {
        lines.add((__pytra_str(__pytra_str(__pytra_str("let v") + __pytra_str(i)) + __pytra_str(" = ")) + __pytra_str(i + 1L)))
        i += 1L
    }
    i = __pytra_int(0L)
    while (i < __pytra_int(loops)) {
        var x: Long = (i % var_count)
        var y: Long = ((i + 3L) % var_count)
        var c1: Long = ((i % 7L) + 1L)
        var c2: Long = ((i % 11L) + 2L)
        lines.add((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str(__pytra_str("v") + __pytra_str(x)) + __pytra_str(" = (v"))) + __pytra_str(x))) + __pytra_str(" * "))) + __pytra_str(c1))) + __pytra_str(" + v"))) + __pytra_str(y))) + __pytra_str(" + 10000) / ") + __pytra_str(c2)))
        if ((__pytra_int(i % 97L) == __pytra_int(0L))) {
            lines.add((__pytra_str("print v") + __pytra_str(x)))
        }
        i += 1L
    }
    lines.add("print (v0 + v1 + v2 + v3)")
    return lines
}

fun run_demo() {
    var demo_lines: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    demo_lines.add("let a = 10")
    demo_lines.add("let b = 3")
    demo_lines.add("a = (a + b) * 2")
    demo_lines.add("print a")
    demo_lines.add("print a / b")
    var tokens: MutableList<Any?> = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = __pytra_as_Parser(Parser(tokens))
    var stmts: MutableList<Any?> = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

fun run_benchmark() {
    var source_lines: MutableList<Any?> = __pytra_as_list(build_benchmark_source(32L, 120000L))
    var start: Double = __pytra_perf_counter()
    var tokens: MutableList<Any?> = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = __pytra_as_Parser(Parser(tokens))
    var stmts: MutableList<Any?> = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("token_count:", __pytra_len(tokens))
    __pytra_print("expr_count:", __pytra_len(parser.expr_nodes))
    __pytra_print("stmt_count:", __pytra_len(stmts))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

fun __pytra_main() {
    run_demo()
    run_benchmark()
}

fun main(args: Array<String>) {
    __pytra_main()
}
