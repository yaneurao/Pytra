// Auto-generated Pytra Scala 3 native source from EAST3.
import scala.collection.mutable
import scala.util.boundary, boundary.break
import scala.math.*
import java.nio.file.{Files, Paths}


def __pytra_is_Token(v: Any): Boolean = {
    v.isInstanceOf[Token]
}

def __pytra_as_Token(v: Any): Token = {
    v match {
        case obj: Token => obj
        case _ => new Token()
    }
}

def __pytra_is_ExprNode(v: Any): Boolean = {
    v.isInstanceOf[ExprNode]
}

def __pytra_as_ExprNode(v: Any): ExprNode = {
    v match {
        case obj: ExprNode => obj
        case _ => new ExprNode()
    }
}

def __pytra_is_StmtNode(v: Any): Boolean = {
    v.isInstanceOf[StmtNode]
}

def __pytra_as_StmtNode(v: Any): StmtNode = {
    v match {
        case obj: StmtNode => obj
        case _ => new StmtNode()
    }
}

def __pytra_is_Parser(v: Any): Boolean = {
    v.isInstanceOf[Parser]
}

def __pytra_as_Parser(v: Any): Parser = {
    v match {
        case obj: Parser => obj
        case _ => new Parser()
    }
}

class Token() {
    var kind: String = ""
    var text: String = ""
    var pos: Long = 0L
    var number_value: Long = 0L

    def this(kind: String, text: String, pos: Long, number_value: Long) = {
        this()
        this.kind = kind
        this.text = text
        this.pos = pos
        this.number_value = number_value
    }
}

class ExprNode() {
    var kind: String = ""
    var value: Long = 0L
    var name: String = ""
    var op: String = ""
    var left: Long = 0L
    var right: Long = 0L
    var kind_tag: Long = 0L
    var op_tag: Long = 0L

    def this(kind: String, value: Long, name: String, op: String, left: Long, right: Long, kind_tag: Long, op_tag: Long) = {
        this()
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

class StmtNode() {
    var kind: String = ""
    var name: String = ""
    var expr_index: Long = 0L
    var kind_tag: Long = 0L

    def this(kind: String, name: String, expr_index: Long, kind_tag: Long) = {
        this()
        this.kind = kind
        this.name = name
        this.expr_index = expr_index
        this.kind_tag = kind_tag
    }
}

class Parser() {
    var tokens: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()
    var pos: Long = 0L
    var expr_nodes: mutable.ArrayBuffer[Any] = mutable.ArrayBuffer[Any]()

    def new_expr_nodes(): mutable.ArrayBuffer[Any] = {
        return __pytra_as_list(mutable.ArrayBuffer[Any]())
    }

    def this(tokens: mutable.ArrayBuffer[Any]) = {
        this()
        this.tokens = tokens
        this.pos = 0L
        this.expr_nodes = this.new_expr_nodes()
    }

    def current_token(): Token = {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, this.pos)))
    }

    def previous_token(): Token = {
        return __pytra_as_Token(__pytra_as_Token(__pytra_get_index(this.tokens, (this.pos - 1L))))
    }

    def peek_kind(): String = {
        return __pytra_str(this.current_token().kind)
    }

    def py_match(kind: String): Boolean = {
        if ((__pytra_str(this.peek_kind()) == __pytra_str(kind))) {
            this.pos += 1L
            return true
        }
        return false
    }

    def expect(kind: String): Token = {
        var token: Token = __pytra_as_Token(this.current_token())
        if ((__pytra_str(token.kind) != __pytra_str(kind))) {
            throw new RuntimeException(__pytra_str(((__pytra_str(__pytra_str(__pytra_str(__pytra_str("parse error at pos=") + __pytra_str(token.pos)) + __pytra_str(", expected=")) + __pytra_str(kind)) + __pytra_str(", got=")) + token.kind)))
        }
        this.pos += 1L
        return token
    }

    def skip_newlines(): Unit = {
        while (this.py_match("NEWLINE")) {
            // pass
        }
    }

    def add_expr(node: ExprNode): Long = {
        this.expr_nodes = __pytra_as_list(this.expr_nodes); this.expr_nodes.append(node)
        return (__pytra_len(this.expr_nodes) - 1L)
    }

    def parse_program(): mutable.ArrayBuffer[Any] = {
        var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
        this.skip_newlines()
        while ((__pytra_str(this.peek_kind()) != __pytra_str("EOF"))) {
            var stmt: StmtNode = __pytra_as_StmtNode(this.parse_stmt())
            stmts.append(stmt)
            this.skip_newlines()
        }
        return stmts
    }

    def parse_stmt(): StmtNode = {
        if (this.py_match("LET")) {
            var let_name: String = __pytra_str(this.expect("IDENT").text)
            this.expect("EQUAL")
            var let_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(new StmtNode("let", let_name, let_expr_index, 1L))
        }
        if (this.py_match("PRINT")) {
            var print_expr_index: Long = __pytra_int(this.parse_expr())
            return __pytra_as_StmtNode(new StmtNode("print", "", print_expr_index, 3L))
        }
        var assign_name: String = __pytra_str(this.expect("IDENT").text)
        this.expect("EQUAL")
        var assign_expr_index: Long = __pytra_int(this.parse_expr())
        return __pytra_as_StmtNode(new StmtNode("assign", assign_name, assign_expr_index, 2L))
    }

    def parse_expr(): Long = {
        return __pytra_int(this.parse_add())
    }

    def parse_add(): Long = {
        var left: Long = __pytra_int(this.parse_mul())
        while (true) {
            if (this.py_match("PLUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "+", left, right, 3L, 1L)))
                throw new RuntimeException("pytra continue outside loop")
            }
            if (this.py_match("MINUS")) {
                var right: Long = __pytra_int(this.parse_mul())
                left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "-", left, right, 3L, 2L)))
                throw new RuntimeException("pytra continue outside loop")
            }
            throw new RuntimeException("pytra break outside loop")
        }
        return left
    }

    def parse_mul(): Long = {
        var left: Long = __pytra_int(this.parse_unary())
        while (true) {
            if (this.py_match("STAR")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "*", left, right, 3L, 3L)))
                throw new RuntimeException("pytra continue outside loop")
            }
            if (this.py_match("SLASH")) {
                var right: Long = __pytra_int(this.parse_unary())
                left = __pytra_int(this.add_expr(new ExprNode("bin", 0L, "", "/", left, right, 3L, 4L)))
                throw new RuntimeException("pytra continue outside loop")
            }
            throw new RuntimeException("pytra break outside loop")
        }
        return left
    }

    def parse_unary(): Long = {
        if (this.py_match("MINUS")) {
            var child: Long = __pytra_int(this.parse_unary())
            return __pytra_int(this.add_expr(new ExprNode("neg", 0L, "", "", child, (-1L), 4L, 0L)))
        }
        return __pytra_int(this.parse_primary())
    }

    def parse_primary(): Long = {
        if (this.py_match("NUMBER")) {
            var token_num: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(new ExprNode("lit", token_num.number_value, "", "", (-1L), (-1L), 1L, 0L)))
        }
        if (this.py_match("IDENT")) {
            var token_ident: Token = __pytra_as_Token(this.previous_token())
            return __pytra_int(this.add_expr(new ExprNode("var", 0L, token_ident.text, "", (-1L), (-1L), 2L, 0L)))
        }
        if (this.py_match("LPAREN")) {
            var expr_index: Long = __pytra_int(this.parse_expr())
            this.expect("RPAREN")
            return expr_index
        }
        var t: Token = __pytra_as_Token(this.current_token())
        throw new RuntimeException(__pytra_str(((__pytra_str(__pytra_str("primary parse error at pos=") + __pytra_str(t.pos)) + __pytra_str(" got=")) + t.kind)))
        return 0L
    }
}

def tokenize(lines: mutable.ArrayBuffer[String]): mutable.ArrayBuffer[Any] = {
    var single_char_token_tags: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]((__pytra_str("+"), 1L), (__pytra_str("-"), 2L), (__pytra_str("*"), 3L), (__pytra_str("/"), 4L), (__pytra_str("("), 5L), (__pytra_str(")"), 6L), (__pytra_str("="), 7L)))
    var single_char_token_kinds: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[String]("PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL")
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(mutable.ArrayBuffer[Any]())
    val __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val __it_2 = __iter_0(__i_1.toInt)
        val __tuple_3 = __pytra_as_list(__it_2)
        var line_index: Long = __pytra_int(__tuple_3(0))
        var source: String = __pytra_str(__tuple_3(1))
        var i: Long = 0L
        var n: Long = __pytra_len(source)
        while ((i < n)) {
            var ch: String = __pytra_str(__pytra_get_index(source, i))
            if ((__pytra_str(ch) == __pytra_str(" "))) {
                i += 1L
                throw new RuntimeException("pytra continue outside loop")
            }
            var single_tag: Long = __pytra_int(__pytra_as_dict(single_char_token_tags).getOrElse(__pytra_str(ch), 0L))
            if ((single_tag > 0L)) {
                tokens.append(new Token(__pytra_str(__pytra_get_index(single_char_token_kinds, (single_tag - 1L))), ch, i, 0L))
                i += 1L
                throw new RuntimeException("pytra continue outside loop")
            }
            if (__pytra_truthy(__pytra_isdigit(ch))) {
                var start: Long = i
                while (((i < n) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i)))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                tokens.append(new Token("NUMBER", text, start, __pytra_int(text)))
                throw new RuntimeException("pytra continue outside loop")
            }
            if ((__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_")))) {
                var start: Long = i
                while (((i < n) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_get_index(source, i)))) || (__pytra_str(__pytra_get_index(source, i)) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i))))))) {
                    i += 1L
                }
                var text: String = __pytra_str(__pytra_slice(source, start, i))
                if ((__pytra_str(text) == __pytra_str("let"))) {
                    tokens.append(new Token("LET", text, start, 0L))
                } else {
                    if ((__pytra_str(text) == __pytra_str("print"))) {
                        tokens.append(new Token("PRINT", text, start, 0L))
                    } else {
                        tokens.append(new Token("IDENT", text, start, 0L))
                    }
                }
                throw new RuntimeException("pytra continue outside loop")
            }
            throw new RuntimeException(__pytra_str((__pytra_str(__pytra_str(__pytra_str(__pytra_str(__pytra_str("tokenize error at line=") + __pytra_str(line_index)) + __pytra_str(" pos=")) + __pytra_str(i)) + __pytra_str(" ch=")) + __pytra_str(ch))))
        }
        tokens.append(new Token("NEWLINE", "", n, 0L))
        __i_1 += 1L
    }
    tokens.append(new Token("EOF", "", __pytra_len(lines), 0L))
    return tokens
}

def eval_expr(expr_index: Long, expr_nodes: mutable.ArrayBuffer[Any], env: mutable.LinkedHashMap[Any, Any]): Long = {
    var node: ExprNode = __pytra_as_ExprNode(__pytra_as_ExprNode(__pytra_get_index(expr_nodes, expr_index)))
    if ((__pytra_int(node.kind_tag) == 1L)) {
        return __pytra_int(node.value)
    }
    if ((__pytra_int(node.kind_tag) == 2L)) {
        if ((!(__pytra_contains(env, node.name)))) {
            throw new RuntimeException(__pytra_str(("undefined variable: " + node.name)))
        }
        return __pytra_int(__pytra_get_index(env, node.name))
    }
    if ((__pytra_int(node.kind_tag) == 4L)) {
        return __pytra_int(-eval_expr(node.left, expr_nodes, env))
    }
    if ((__pytra_int(node.kind_tag) == 3L)) {
        var lhs: Long = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Long = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if ((__pytra_int(node.op_tag) == 1L)) {
            return (lhs + rhs)
        }
        if ((__pytra_int(node.op_tag) == 2L)) {
            return (lhs - rhs)
        }
        if ((__pytra_int(node.op_tag) == 3L)) {
            return (lhs * rhs)
        }
        if ((__pytra_int(node.op_tag) == 4L)) {
            if ((rhs == 0L)) {
                throw new RuntimeException(__pytra_str("division by zero"))
            }
            return (__pytra_int(lhs / rhs))
        }
        throw new RuntimeException(__pytra_str(("unknown operator: " + node.op)))
    }
    throw new RuntimeException(__pytra_str(("unknown node kind: " + node.kind)))
    return 0L
}

def execute(stmts: mutable.ArrayBuffer[Any], expr_nodes: mutable.ArrayBuffer[Any], trace: Boolean): Long = {
    var env: mutable.LinkedHashMap[Any, Any] = __pytra_as_dict(mutable.LinkedHashMap[Any, Any]())
    var checksum: Long = 0L
    var printed: Long = 0L
    val __iter_0 = __pytra_as_list(stmts)
    var __i_1: Long = 0L
    while (__i_1 < __iter_0.size.toLong) {
        val stmt: StmtNode = __pytra_as_StmtNode(__iter_0(__i_1.toInt))
        if ((__pytra_int(stmt.kind_tag) == 1L)) {
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            throw new RuntimeException("pytra continue outside loop")
        }
        if ((__pytra_int(stmt.kind_tag) == 2L)) {
            if ((!(__pytra_contains(env, stmt.name)))) {
                throw new RuntimeException(__pytra_str(("assign to undefined variable: " + stmt.name)))
            }
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            throw new RuntimeException("pytra continue outside loop")
        }
        var value: Long = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
        if (trace) {
            __pytra_print(value)
        }
        var norm: Long = (value % 1000000007L)
        if ((norm < 0L)) {
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

def build_benchmark_source(var_count: Long, loops: Long): mutable.ArrayBuffer[String] = {
    var lines: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[Any]()
    var i: Long = 0L
    while ((i < var_count)) {
        lines.append((__pytra_str(__pytra_str(__pytra_str("let v") + __pytra_str(i)) + __pytra_str(" = ")) + __pytra_str(i + 1L)))
        i += 1L
    }
    i = 0L
    while ((i < loops)) {
        var x: Long = (i % var_count)
        var y: Long = ((i + 3L) % var_count)
        var c1: Long = ((i % 7L) + 1L)
        var c2: Long = ((i % 11L) + 2L)
        lines.append((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str(__pytra_str("v") + __pytra_str(x)) + __pytra_str(" = (v"))) + __pytra_str(x))) + __pytra_str(" * "))) + __pytra_str(c1))) + __pytra_str(" + v"))) + __pytra_str(y))) + __pytra_str(" + 10000) / ") + __pytra_str(c2)))
        if (((i % 97L) == 0L)) {
            lines.append((__pytra_str("print v") + __pytra_str(x)))
        }
        i += 1L
    }
    lines.append("print (v0 + v1 + v2 + v3)")
    return lines
}

def run_demo(): Unit = {
    var demo_lines: mutable.ArrayBuffer[String] = mutable.ArrayBuffer[Any]()
    demo_lines.append("let a = 10")
    demo_lines.append("let b = 3")
    demo_lines.append("a = (a + b) * 2")
    demo_lines.append("print a")
    demo_lines.append("print a / b")
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = __pytra_as_Parser(new Parser(tokens))
    var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

def run_benchmark(): Unit = {
    var source_lines: mutable.ArrayBuffer[String] = build_benchmark_source(32L, 120000L)
    var start: Double = __pytra_perf_counter()
    var tokens: mutable.ArrayBuffer[Any] = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = __pytra_as_Parser(new Parser(tokens))
    var stmts: mutable.ArrayBuffer[Any] = __pytra_as_list(parser.parse_program())
    var checksum: Long = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = (__pytra_perf_counter() - start)
    __pytra_print("token_count:", __pytra_len(tokens))
    __pytra_print("expr_count:", __pytra_len(parser.expr_nodes))
    __pytra_print("stmt_count:", __pytra_len(stmts))
    __pytra_print("checksum:", checksum)
    __pytra_print("elapsed_sec:", elapsed)
}

def __pytra_main(): Unit = {
    run_demo()
    run_benchmark()
}

def main(args: Array[String]): Unit = {
    __pytra_main()
}