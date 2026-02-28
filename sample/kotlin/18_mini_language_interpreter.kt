import kotlin.math.*

fun __pytra_noop(vararg args: Any?) { }

fun __pytra_any_default(): Any? {
    return 0L
}

fun __pytra_assert(vararg args: Any?): String {
    return "True"
}

fun __pytra_perf_counter(): Double {
    return System.nanoTime().toDouble() / 1_000_000_000.0
}

fun __pytra_truthy(v: Any?): Boolean {
    if (v == null) return false
    if (v is Boolean) return v
    if (v is Long) return v != 0L
    if (v is Int) return v != 0
    if (v is Double) return v != 0.0
    if (v is String) return v.isNotEmpty()
    if (v is List<*>) return v.isNotEmpty()
    if (v is Map<*, *>) return v.isNotEmpty()
    return true
}

fun __pytra_int(v: Any?): Long {
    if (v == null) return 0L
    if (v is Long) return v
    if (v is Int) return v.toLong()
    if (v is Double) return v.toLong()
    if (v is Boolean) return if (v) 1L else 0L
    if (v is String) return v.toLongOrNull() ?: 0L
    return 0L
}

fun __pytra_float(v: Any?): Double {
    if (v == null) return 0.0
    if (v is Double) return v
    if (v is Float) return v.toDouble()
    if (v is Long) return v.toDouble()
    if (v is Int) return v.toDouble()
    if (v is Boolean) return if (v) 1.0 else 0.0
    if (v is String) return v.toDoubleOrNull() ?: 0.0
    return 0.0
}

fun __pytra_str(v: Any?): String {
    if (v == null) return ""
    return v.toString()
}

fun __pytra_len(v: Any?): Long {
    if (v == null) return 0L
    if (v is String) return v.length.toLong()
    if (v is List<*>) return v.size.toLong()
    if (v is Map<*, *>) return v.size.toLong()
    return 0L
}

fun __pytra_index(i: Long, n: Long): Long {
    if (i < 0L) return i + n
    return i
}

fun __pytra_get_index(container: Any?, index: Any?): Any? {
    if (container is List<*>) {
        if (container.isEmpty()) return __pytra_any_default()
        val i = __pytra_index(__pytra_int(index), container.size.toLong())
        if (i < 0L || i >= container.size.toLong()) return __pytra_any_default()
        return container[i.toInt()]
    }
    if (container is Map<*, *>) {
        return container[__pytra_str(index)] ?: __pytra_any_default()
    }
    if (container is String) {
        if (container.isEmpty()) return ""
        val chars = container.toCharArray()
        val i = __pytra_index(__pytra_int(index), chars.size.toLong())
        if (i < 0L || i >= chars.size.toLong()) return ""
        return chars[i.toInt()].toString()
    }
    return __pytra_any_default()
}

fun __pytra_set_index(container: Any?, index: Any?, value: Any?) {
    if (container is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        val list = container as MutableList<Any?>
        if (list.isEmpty()) return
        val i = __pytra_index(__pytra_int(index), list.size.toLong())
        if (i < 0L || i >= list.size.toLong()) return
        list[i.toInt()] = value
        return
    }
    if (container is MutableMap<*, *>) {
        @Suppress("UNCHECKED_CAST")
        val map = container as MutableMap<Any, Any?>
        map[__pytra_str(index)] = value
    }
}

fun __pytra_slice(container: Any?, lower: Any?, upper: Any?): Any? {
    if (container is String) {
        val n = container.length.toLong()
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if (lo < 0L) lo = 0L
        if (hi < 0L) hi = 0L
        if (lo > n) lo = n
        if (hi > n) hi = n
        if (hi < lo) hi = lo
        return container.substring(lo.toInt(), hi.toInt())
    }
    if (container is List<*>) {
        val n = container.size.toLong()
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if (lo < 0L) lo = 0L
        if (hi < 0L) hi = 0L
        if (lo > n) lo = n
        if (hi > n) hi = n
        if (hi < lo) hi = lo
        @Suppress("UNCHECKED_CAST")
        return container.subList(lo.toInt(), hi.toInt()).toMutableList() as MutableList<Any?>
    }
    return __pytra_any_default()
}

fun __pytra_isdigit(v: Any?): Boolean {
    val s = __pytra_str(v)
    if (s.isEmpty()) return false
    return s.all { it.isDigit() }
}

fun __pytra_isalpha(v: Any?): Boolean {
    val s = __pytra_str(v)
    if (s.isEmpty()) return false
    return s.all { it.isLetter() }
}

fun __pytra_contains(container: Any?, value: Any?): Boolean {
    if (container is List<*>) {
        val needle = __pytra_str(value)
        for (item in container) {
            if (__pytra_str(item) == needle) return true
        }
        return false
    }
    if (container is Map<*, *>) {
        return container.containsKey(__pytra_str(value))
    }
    if (container is String) {
        return container.contains(__pytra_str(value))
    }
    return false
}

fun __pytra_ifexp(cond: Boolean, a: Any?, b: Any?): Any? {
    return if (cond) a else b
}

fun __pytra_bytearray(initValue: Any?): MutableList<Any?> {
    if (initValue is Long) {
        val out = mutableListOf<Any?>()
        var i = 0L
        while (i < initValue) {
            out.add(0L)
            i += 1L
        }
        return out
    }
    if (initValue is Int) {
        val out = mutableListOf<Any?>()
        var i = 0
        while (i < initValue) {
            out.add(0L)
            i += 1
        }
        return out
    }
    if (initValue is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return (initValue as MutableList<Any?>).toMutableList()
    }
    if (initValue is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (initValue as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_bytes(v: Any?): MutableList<Any?> {
    if (v is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as MutableList<Any?>).toMutableList()
    }
    if (v is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_list_repeat(value: Any?, count: Any?): MutableList<Any?> {
    val out = mutableListOf<Any?>()
    val n = __pytra_int(count)
    var i = 0L
    while (i < n) {
        out.add(value)
        i += 1L
    }
    return out
}

fun __pytra_enumerate(v: Any?): MutableList<Any?> {
    val items = __pytra_as_list(v)
    val out = mutableListOf<Any?>()
    var i = 0L
    while (i < items.size.toLong()) {
        out.add(mutableListOf(i, items[i.toInt()]))
        i += 1L
    }
    return out
}

fun __pytra_as_list(v: Any?): MutableList<Any?> {
    if (v is MutableList<*>) {
        @Suppress("UNCHECKED_CAST")
        return v as MutableList<Any?>
    }
    if (v is List<*>) {
        @Suppress("UNCHECKED_CAST")
        return (v as List<Any?>).toMutableList()
    }
    return mutableListOf()
}

fun __pytra_as_dict(v: Any?): MutableMap<Any, Any?> {
    if (v is MutableMap<*, *>) {
        @Suppress("UNCHECKED_CAST")
        return v as MutableMap<Any, Any?>
    }
    if (v is Map<*, *>) {
        val out = mutableMapOf<Any, Any?>()
        for ((k, valAny) in v) {
            if (k != null) out[k] = valAny
        }
        return out
    }
    return mutableMapOf()
}

fun __pytra_pop_last(v: MutableList<Any?>): MutableList<Any?> {
    if (v.isEmpty()) return v
    v.removeAt(v.size - 1)
    return v
}

fun __pytra_print(vararg args: Any?) {
    if (args.isEmpty()) {
        println()
        return
    }
    println(args.joinToString(" ") { __pytra_str(it) })
}

fun __pytra_min(a: Any?, b: Any?): Any? {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af < bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    return __pytra_int(b)
}

fun __pytra_max(a: Any?, b: Any?): Any? {
    val af = __pytra_float(a)
    val bf = __pytra_float(b)
    if (af > bf) {
        if (__pytra_is_float(a) || __pytra_is_float(b)) return af
        return __pytra_int(a)
    }
    if (__pytra_is_float(a) || __pytra_is_float(b)) return bf
    return __pytra_int(b)
}

fun __pytra_is_int(v: Any?): Boolean {
    return (v is Long) || (v is Int)
}

fun __pytra_is_float(v: Any?): Boolean {
    return v is Double
}

fun __pytra_is_bool(v: Any?): Boolean {
    return v is Boolean
}

fun __pytra_is_str(v: Any?): Boolean {
    return v is String
}

fun __pytra_is_list(v: Any?): Boolean {
    return v is List<*>
}

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

    constructor(kind: String, text: String, pos: Long) : this() {
        this.kind = kind
        this.text = text
        this.pos = pos
    }
}

open class ExprNode() {
    var kind: String = ""
    var value: Long = 0L
    var name: String = ""
    var op: String = ""
    var left: Long = 0L
    var right: Long = 0L

    constructor(kind: String, value: Long, name: String, op: String, left: Long, right: Long) : this() {
        this.kind = kind
        this.value = value
        this.name = name
        this.op = op
        this.left = left
        this.right = right
    }
}

open class StmtNode() {
    var kind: String = ""
    var name: String = ""
    var expr_index: Long = 0L

    constructor(kind: String, name: String, expr_index: Long) : this() {
        this.kind = kind
        this.name = name
        this.expr_index = expr_index
    }
}

open class Parser() {
    var tokens: MutableList<Any?> = mutableListOf()
    var pos: Long = 0L
    var expr_nodes: MutableList<Any?> = mutableListOf()

    fun new_expr_nodes(): MutableList<Any?> {
        return __pytra_as_list(mutableListOf<Any?>())
    }

    constructor(tokens: MutableList<Any?>) : this() {
        this.tokens = tokens
        this.pos = 0L
        this.expr_nodes = this.new_expr_nodes()
    }

    fun peek_kind(): String {
        return __pytra_str(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)).kind)
    }

    fun match(kind: String): Boolean {
        if ((__pytra_str(this.peek_kind()) == __pytra_str(kind))) {
            this.pos += 1L
            return __pytra_truthy(true)
        }
        return __pytra_truthy(false)
    }

    fun expect(kind: String): Token {
        if ((__pytra_str(this.peek_kind()) != __pytra_str(kind))) {
            var t: Token = __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
            throw RuntimeException(__pytra_str(((__pytra_str((__pytra_str((__pytra_str((__pytra_str("parse error at pos=") + __pytra_str(__pytra_str(t.pos)))) + __pytra_str(", expected="))) + __pytra_str(kind))) + __pytra_str(", got=")) + t.kind)))
        }
        var token: Token = __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
        this.pos += 1L
        return __pytra_as_Token(token)
    }

    fun skip_newlines() {
        while (this.match("NEWLINE")) {
            run { }
        }
    }

    fun add_expr(node: ExprNode): Long {
        this.expr_nodes = __pytra_as_list(this.expr_nodes); this.expr_nodes.add(node)
        return __pytra_int((__pytra_int(__pytra_len(this.expr_nodes)) - __pytra_int(1L)))
    }

    fun parse_program(): MutableList<Any?> {
        var stmts: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
        this.skip_newlines()
        while ((__pytra_str(this.peek_kind()) != __pytra_str("EOF"))) {
            var stmt: StmtNode = __pytra_as_StmtNode(this.parse_stmt())
            stmts = __pytra_as_list(stmts); stmts.add(stmt)
            this.skip_newlines()
        }
        return __pytra_as_list(stmts)
    }

    fun parse_stmt(): StmtNode {
        if (this.match("LET")) {
            var let_name: String = __pytra_str(this.expect("IDENT").text)
            this.expect("EQUAL")
            var let_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(StmtNode("let", let_name, let_expr_index))
        }
        if (this.match("PRINT")) {
            var print_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(StmtNode("print", "", print_expr_index))
        }
        var assign_name: String = __pytra_str(this.expect("IDENT").text)
        this.expect("EQUAL")
        var assign_expr_index: Long = __pytra_int(this.parse_expr())
        return __pytra_as_StmtNode(StmtNode("assign", assign_name, assign_expr_index))
    }

    fun parse_expr(): Long {
        return __pytra_int(this.parse_add())
    }

    fun parse_add(): Long {
        var left: Long = __pytra_int(this.parse_mul())
        while (true) {
            if (this.match("PLUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "+", left, right)))
                continue
            }
            if (this.match("MINUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "-", left, right)))
                continue
            }
            break
        }
        return __pytra_int(left)
    }

    fun parse_mul(): Long {
        var left: Long = __pytra_int(this.parse_unary())
        while (true) {
            if (this.match("STAR")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "*", left, right)))
                continue
            }
            if (this.match("SLASH")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(ExprNode("bin", 0L, "", "/", left, right)))
                continue
            }
            break
        }
        return __pytra_int(left)
    }

    fun parse_unary(): Long {
        if (this.match("MINUS")) {
            var child: Long = __pytra_int(this.parse_unary())
            return __pytra_int(this.add_expr(ExprNode("neg", 0L, "", "", child, (-1L))))
        }
        return __pytra_int(this.parse_primary())
    }

    fun parse_primary(): Long {
        if (this.match("NUMBER")) {
            var token_num: Token = __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, (__pytra_int(this.pos) - __pytra_int(1L)))))
            return __pytra_int(this.add_expr(ExprNode("lit", __pytra_int(token_num.text), "", "", (-1L), (-1L))))
        }
        if (this.match("IDENT")) {
            var token_ident: Token = __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, (__pytra_int(this.pos) - __pytra_int(1L)))))
            return __pytra_int(this.add_expr(ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L))))
        }
        if (this.match("LPAREN")) {
            var expr_index: Long = __pytra_int(this.parse_expr())
            this.expect("RPAREN")
            return __pytra_int(expr_index)
        }
        var t: Token = __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
        throw RuntimeException(__pytra_str(((__pytra_str((__pytra_str("primary parse error at pos=") + __pytra_str(__pytra_str(t.pos)))) + __pytra_str(" got=")) + t.kind)))
        return 0L
    }
}

fun tokenize(lines: MutableList<Any?>): MutableList<Any?> {
    var tokens: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val __it_2 = __iter_0[__i_1.toInt()]
        val __tuple_3 = __pytra_as_list(__it_2)
        var line_index: Long = __pytra_int(__tuple_3[0])
        var source: String = __pytra_str(__tuple_3[1])
        var i: Long = __pytra_int(0L)
        var n: Long = __pytra_int(__pytra_len(source))
        while ((__pytra_int(i) < __pytra_int(n))) {
            var ch: String = __pytra_str(__pytra_str(__pytra_get_index(source, i)))
            if ((__pytra_str(ch) == __pytra_str(" "))) {
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("+"))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("PLUS", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("-"))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("MINUS", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("*"))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("STAR", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("/"))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("SLASH", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("("))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("LPAREN", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str(")"))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("RPAREN", ch, i))
                i += 1L
                continue
            }
            if ((__pytra_str(ch) == __pytra_str("="))) {
                tokens = __pytra_as_list(tokens); tokens.add(Token("EQUAL", ch, i))
                i += 1L
                continue
            }
            if (__pytra_truthy(__pytra_isdigit(ch))) {
                var start: Long = __pytra_int(i)
                while (((__pytra_int(i) < __pytra_int(n)) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i)))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                tokens = __pytra_as_list(tokens); tokens.add(Token("NUMBER", text, start))
                continue
            }
            if ((__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_")))) {
                var start: Long = __pytra_int(i)
                while (((__pytra_int(i) < __pytra_int(n)) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_get_index(source, i)))) || (__pytra_str(__pytra_str(__pytra_get_index(source, i))) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i))))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                if ((__pytra_str(text) == __pytra_str("let"))) {
                    tokens = __pytra_as_list(tokens); tokens.add(Token("LET", text, start))
                } else {
                    if ((__pytra_str(text) == __pytra_str("print"))) {
                        tokens = __pytra_as_list(tokens); tokens.add(Token("PRINT", text, start))
                    } else {
                        tokens = __pytra_as_list(tokens); tokens.add(Token("IDENT", text, start))
                    }
                }
                continue
            }
            throw RuntimeException(__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("tokenize error at line=") + __pytra_str(__pytra_str(line_index)))) + __pytra_str(" pos="))) + __pytra_str(__pytra_str(i)))) + __pytra_str(" ch="))) + __pytra_str(ch))))
        }
        tokens = __pytra_as_list(tokens); tokens.add(Token("NEWLINE", "", n))
        __i_1 += 1L
    }
    tokens = __pytra_as_list(tokens); tokens.add(Token("EOF", "", __pytra_len(lines)))
    return __pytra_as_list(tokens)
}

fun eval_expr(expr_index: Long, expr_nodes: MutableList<Any?>, env: MutableMap<Any, Any?>): Long {
    var node: ExprNode = __pytra_as_ExprNode(__pytra_as_ExprNode(__pytra_get_index(expr_nodes, expr_index)))
    if ((__pytra_str(node.kind) == __pytra_str("lit"))) {
        return __pytra_int(node.value)
    }
    if ((__pytra_str(node.kind) == __pytra_str("var"))) {
        if ((!(__pytra_contains(env, node.name)))) {
            throw RuntimeException(__pytra_str(("undefined variable: " + node.name)))
        }
        return __pytra_int(__pytra_int(__pytra_get_index(env, node.name)))
    }
    if ((__pytra_str(node.kind) == __pytra_str("neg"))) {
        return __pytra_int((-eval_expr(node.left, expr_nodes, env)))
    }
    if ((__pytra_str(node.kind) == __pytra_str("bin"))) {
        var lhs: Long = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Long = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if ((__pytra_str(node.op) == __pytra_str("+"))) {
            return __pytra_int((__pytra_int(lhs) + __pytra_int(rhs)))
        }
        if ((__pytra_str(node.op) == __pytra_str("-"))) {
            return __pytra_int((__pytra_int(lhs) - __pytra_int(rhs)))
        }
        if ((__pytra_str(node.op) == __pytra_str("*"))) {
            return __pytra_int((__pytra_int(lhs) * __pytra_int(rhs)))
        }
        if ((__pytra_str(node.op) == __pytra_str("/"))) {
            if ((__pytra_int(rhs) == __pytra_int(0L))) {
                throw RuntimeException(__pytra_str("division by zero"))
            }
            return __pytra_int((__pytra_int(__pytra_int(lhs) / __pytra_int(rhs))))
        }
        throw RuntimeException(__pytra_str(("unknown operator: " + node.op)))
    }
    throw RuntimeException(__pytra_str(("unknown node kind: " + node.kind)))
    return 0L
}

fun execute(stmts: MutableList<Any?>, expr_nodes: MutableList<Any?>, trace: Boolean): Long {
    var env: MutableMap<Any, Any?> = __pytra_as_dict(mutableMapOf<Any, Any?>())
    var checksum: Long = __pytra_int(0L)
    var printed: Long = __pytra_int(0L)
    val __iter_0 = __pytra_as_list(stmts)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong()) {
        val stmt: StmtNode = __pytra_as_StmtNode(__iter_0[__i_1.toInt()])
        if ((__pytra_str(stmt.kind) == __pytra_str("let"))) {
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            __i_1 += 1L
            continue
        }
        if ((__pytra_str(stmt.kind) == __pytra_str("assign"))) {
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
        var norm: Long = __pytra_int((__pytra_int(value) % __pytra_int(1000000007L)))
        if ((__pytra_int(norm) < __pytra_int(0L))) {
            norm += 1000000007L
        }
        checksum = __pytra_int((__pytra_int((__pytra_int((__pytra_int(checksum) * __pytra_int(131L))) + __pytra_int(norm))) % __pytra_int(1000000007L)))
        printed += 1L
        __i_1 += 1L
    }
    if (trace) {
        __pytra_print("printed:", printed)
    }
    return __pytra_int(checksum)
}

fun build_benchmark_source(var_count: Long, loops: Long): MutableList<Any?> {
    var lines: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    val __step_0 = __pytra_int(1L)
    var i = __pytra_int(0L)
    while ((__step_0 >= 0L && i < __pytra_int(var_count)) || (__step_0 < 0L && i > __pytra_int(var_count))) {
        lines = __pytra_as_list(lines); lines.add((__pytra_str((__pytra_str((__pytra_str("let v") + __pytra_str(__pytra_str(i)))) + __pytra_str(" = "))) + __pytra_str(__pytra_str((__pytra_int(i) + __pytra_int(1L))))))
        i += __step_0
    }
    val __step_1 = __pytra_int(1L)
    i = __pytra_int(0L)
    while ((__step_1 >= 0L && i < __pytra_int(loops)) || (__step_1 < 0L && i > __pytra_int(loops))) {
        var x: Long = __pytra_int((__pytra_int(i) % __pytra_int(var_count)))
        var y: Long = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(3L))) % __pytra_int(var_count)))
        var c1: Long = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(7L))) + __pytra_int(1L)))
        var c2: Long = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(11L))) + __pytra_int(2L)))
        lines = __pytra_as_list(lines); lines.add((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("v") + __pytra_str(__pytra_str(x)))) + __pytra_str(" = (v"))) + __pytra_str(__pytra_str(x)))) + __pytra_str(" * "))) + __pytra_str(__pytra_str(c1)))) + __pytra_str(" + v"))) + __pytra_str(__pytra_str(y)))) + __pytra_str(" + 10000) / "))) + __pytra_str(__pytra_str(c2))))
        if ((__pytra_int((__pytra_int(i) % __pytra_int(97L))) == __pytra_int(0L))) {
            lines = __pytra_as_list(lines); lines.add((__pytra_str("print v") + __pytra_str(__pytra_str(x))))
        }
        i += __step_1
    }
    lines = __pytra_as_list(lines); lines.add("print (v0 + v1 + v2 + v3)")
    return __pytra_as_list(lines)
}

fun run_demo() {
    var demo_lines: MutableList<Any?> = __pytra_as_list(mutableListOf<Any?>())
    demo_lines = __pytra_as_list(demo_lines); demo_lines.add("let a = 10")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.add("let b = 3")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.add("a = (a + b) * 2")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.add("print a")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.add("print a / b")
    var tokens: MutableList<Any?> = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = __pytra_as_Parser(Parser(tokens))
    var stmts: MutableList<Any?> = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

fun run_benchmark() {
    var source_lines: MutableList<Any?> = __pytra_as_list(build_benchmark_source(32L, 120000L))
    var start: Double = __pytra_float(__pytra_perf_counter())
    var tokens: MutableList<Any?> = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = __pytra_as_Parser(Parser(tokens))
    var stmts: MutableList<Any?> = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = __pytra_float((__pytra_float(__pytra_perf_counter()) - __pytra_float(start)))
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
