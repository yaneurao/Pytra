// Auto-generated Pytra Swift native source from EAST3.
import Foundation

func __pytra_noop(_ args: Any...) {}

func __pytra_any_default() -> Any {
    return Int64(0)
}

func __pytra_assert(_ args: Any...) -> String {
    _ = args
    return "True"
}

func __pytra_perf_counter() -> Double {
    return Date().timeIntervalSince1970
}

func __pytra_truthy(_ v: Any?) -> Bool {
    guard let value = v else { return false }
    if let b = value as? Bool { return b }
    if let i = value as? Int64 { return i != 0 }
    if let i = value as? Int { return i != 0 }
    if let d = value as? Double { return d != 0.0 }
    if let s = value as? String { return s != "" }
    if let a = value as? [Any] { return !a.isEmpty }
    if let m = value as? [AnyHashable: Any] { return !m.isEmpty }
    return true
}

func __pytra_int(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let i = value as? Int64 { return i }
    if let i = value as? Int { return Int64(i) }
    if let d = value as? Double { return Int64(d) }
    if let b = value as? Bool { return b ? 1 : 0 }
    if let s = value as? String { return Int64(s) ?? 0 }
    return 0
}

func __pytra_float(_ v: Any?) -> Double {
    guard let value = v else { return 0.0 }
    if let d = value as? Double { return d }
    if let f = value as? Float { return Double(f) }
    if let i = value as? Int64 { return Double(i) }
    if let i = value as? Int { return Double(i) }
    if let b = value as? Bool { return b ? 1.0 : 0.0 }
    if let s = value as? String { return Double(s) ?? 0.0 }
    return 0.0
}

func __pytra_str(_ v: Any?) -> String {
    guard let value = v else { return "" }
    if let s = value as? String { return s }
    return String(describing: value)
}

func __pytra_len(_ v: Any?) -> Int64 {
    guard let value = v else { return 0 }
    if let s = value as? String { return Int64(s.count) }
    if let a = value as? [Any] { return Int64(a.count) }
    if let m = value as? [AnyHashable: Any] { return Int64(m.count) }
    return 0
}

func __pytra_index(_ i: Int64, _ n: Int64) -> Int64 {
    if i < 0 {
        return i + n
    }
    return i
}

func __pytra_getIndex(_ container: Any?, _ index: Any?) -> Any {
    if let list = container as? [Any] {
        if list.isEmpty { return __pytra_any_default() }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return __pytra_any_default() }
        return list[Int(i)]
    }
    if let dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        return dict[key] ?? __pytra_any_default()
    }
    if let s = container as? String {
        let chars = Array(s)
        if chars.isEmpty { return "" }
        let i = __pytra_index(__pytra_int(index), Int64(chars.count))
        if i < 0 || i >= Int64(chars.count) { return "" }
        return String(chars[Int(i)])
    }
    return __pytra_any_default()
}

func __pytra_setIndex(_ container: Any?, _ index: Any?, _ value: Any?) {
    if var list = container as? [Any] {
        if list.isEmpty { return }
        let i = __pytra_index(__pytra_int(index), Int64(list.count))
        if i < 0 || i >= Int64(list.count) { return }
        list[Int(i)] = value as Any
        return
    }
    if var dict = container as? [AnyHashable: Any] {
        let key = AnyHashable(__pytra_str(index))
        dict[key] = value
    }
}

func __pytra_slice(_ container: Any?, _ lower: Any?, _ upper: Any?) -> Any {
    if let s = container as? String {
        let chars = Array(s)
        let n = Int64(chars.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return "" }
        return String(chars[Int(lo)..<Int(hi)])
    }
    if let list = container as? [Any] {
        let n = Int64(list.count)
        var lo = __pytra_index(__pytra_int(lower), n)
        var hi = __pytra_index(__pytra_int(upper), n)
        if lo < 0 { lo = 0 }
        if hi < 0 { hi = 0 }
        if lo > n { lo = n }
        if hi > n { hi = n }
        if hi < lo { hi = lo }
        if lo >= hi { return [Any]() }
        return Array(list[Int(lo)..<Int(hi)])
    }
    return __pytra_any_default()
}

func __pytra_isdigit(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.decimalDigits.contains($0) }
}

func __pytra_isalpha(_ v: Any?) -> Bool {
    let s = __pytra_str(v)
    if s.isEmpty { return false }
    return s.unicodeScalars.allSatisfy { CharacterSet.letters.contains($0) }
}

func __pytra_contains(_ container: Any?, _ value: Any?) -> Bool {
    if let list = container as? [Any] {
        let needle = __pytra_str(value)
        for item in list {
            if __pytra_str(item) == needle {
                return true
            }
        }
        return false
    }
    if let dict = container as? [AnyHashable: Any] {
        return dict[AnyHashable(__pytra_str(value))] != nil
    }
    if let s = container as? String {
        let needle = __pytra_str(value)
        return s.contains(needle)
    }
    return false
}

func __pytra_ifexp(_ cond: Bool, _ a: Any, _ b: Any) -> Any {
    return cond ? a : b
}

func __pytra_bytearray(_ initValue: Any?) -> [Any] {
    if let i = initValue as? Int64 {
        return Array(repeating: Int64(0), count: max(0, Int(i)))
    }
    if let i = initValue as? Int {
        return Array(repeating: Int64(0), count: max(0, i))
    }
    if let arr = initValue as? [Any] {
        return arr
    }
    return []
}

func __pytra_bytes(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] {
        return arr
    }
    return []
}

func __pytra_list_repeat(_ value: Any, _ count: Any?) -> [Any] {
    var out: [Any] = []
    var i: Int64 = 0
    let n = __pytra_int(count)
    while i < n {
        out.append(value)
        i += 1
    }
    return out
}

func __pytra_as_list(_ v: Any?) -> [Any] {
    if let arr = v as? [Any] { return arr }
    return []
}

func __pytra_as_u8_list(_ v: Any?) -> [UInt8] {
    if let arr = v as? [UInt8] { return arr }
    return []
}

func __pytra_as_dict(_ v: Any?) -> [AnyHashable: Any] {
    if let dict = v as? [AnyHashable: Any] { return dict }
    return [:]
}

func __pytra_pop_last(_ v: [Any]) -> [Any] {
    if v.isEmpty { return v }
    return Array(v.dropLast())
}

func __pytra_print(_ args: Any...) {
    if args.isEmpty {
        Swift.print()
        return
    }
    Swift.print(args.map { String(describing: $0) }.joined(separator: " "))
}

func __pytra_min(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af < bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_max(_ a: Any?, _ b: Any?) -> Any {
    let af = __pytra_float(a)
    let bf = __pytra_float(b)
    if af > bf {
        if __pytra_is_float(a) || __pytra_is_float(b) { return af }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) { return bf }
    return __pytra_int(b)
}

func __pytra_is_int(_ v: Any?) -> Bool {
    return (v is Int) || (v is Int64)
}

func __pytra_is_float(_ v: Any?) -> Bool {
    return v is Double
}

func __pytra_is_bool(_ v: Any?) -> Bool {
    return v is Bool
}

func __pytra_is_str(_ v: Any?) -> Bool {
    return v is String
}

func __pytra_is_list(_ v: Any?) -> Bool {
    return v is [Any]
}

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

final class Token {
    var kind: String = ""
    var text: String = ""
    var pos: Int64 = 0

    init() {
    }
}

final class ExprNode {
    var kind: String = ""
    var value: Int64 = 0
    var name: String = ""
    var op: String = ""
    var left: Int64 = 0
    var right: Int64 = 0

    init() {
    }
}

final class StmtNode {
    var kind: String = ""
    var name: String = ""
    var expr_index: Int64 = 0

    init() {
    }
}

final class Parser {
    var tokens: [Any] = []
    var pos: Int64 = 0
    var expr_nodes: [Any] = []

    func new_expr_nodes() -> [Any] {
        return []
    }

    init(tokens: [Any]) {
        self.tokens = tokens
        self.pos = Int64(0)
        self.expr_nodes = self.new_expr_nodes()
    }

    func peek_kind() -> String {
        return (__pytra_getIndex(self.tokens, self.pos) as? Token) ?? Token().kind
    }

    func match(kind: String) -> Bool {
        if (__pytra_str(self.peek_kind()) == __pytra_str(kind)) {
            self.pos += Int64(1)
            return true
        }
        return false
    }

    func expect(kind: String) -> Token {
        if (__pytra_str(self.peek_kind()) != __pytra_str(kind)) {
            var t: Token = ((__pytra_getIndex(self.tokens, self.pos) as? Token) ?? Token() as? Token) ?? Token()
            fatalError("pytra raise")
        }
        var token: Token = ((__pytra_getIndex(self.tokens, self.pos) as? Token) ?? Token() as? Token) ?? Token()
        self.pos += Int64(1)
        return token
    }

    func skip_newlines() {
        while self.match("NEWLINE") {
            // pass
        }
    }

    func add_expr(node: ExprNode) -> Int64 {
        self.expr_nodes = __pytra_as_list(self.expr_nodes); self.expr_nodes.append(node)
        return (__pytra_int(__pytra_len(self.expr_nodes)) - __pytra_int(Int64(1)))
    }

    func parse_program() -> [Any] {
        var stmts: [Any] = __pytra_as_list([])
        self.skip_newlines()
        while (__pytra_str(self.peek_kind()) != __pytra_str("EOF")) {
            var stmt: StmtNode = (self.parse_stmt() as? StmtNode) ?? StmtNode()
            stmts = __pytra_as_list(stmts); stmts.append(stmt)
            self.skip_newlines()
        }
        return stmts
    }

    func parse_stmt() -> StmtNode {
        if self.match("LET") {
            var let_name: String = __pytra_str(self.expect("IDENT").text)
            self.expect("EQUAL")
            var let_expr_index: Int64 = __pytra_int(self.parse_expr())
            return StmtNode("let", let_name, let_expr_index)
        }
        if self.match("PRINT") {
            var print_expr_index: Int64 = __pytra_int(self.parse_expr())
            return StmtNode("print", "", print_expr_index)
        }
        var assign_name: String = __pytra_str(self.expect("IDENT").text)
        self.expect("EQUAL")
        var assign_expr_index: Int64 = __pytra_int(self.parse_expr())
        return StmtNode("assign", assign_name, assign_expr_index)
    }

    func parse_expr() -> Int64 {
        return self.parse_add()
    }

    func parse_add() -> Int64 {
        var left: Int64 = __pytra_int(self.parse_mul())
        while true {
            if self.match("PLUS") {
                var right: Int64 = __pytra_int(self.parse_mul())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "+", left, right)))
                continue
            }
            if self.match("MINUS") {
                var right: Int64 = __pytra_int(self.parse_mul())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "-", left, right)))
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
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "*", left, right)))
                continue
            }
            if self.match("SLASH") {
                var right: Int64 = __pytra_int(self.parse_unary())
                left = __pytra_int(self.add_expr(ExprNode("bin", Int64(0), "", "/", left, right)))
                continue
            }
            break
        }
        return left
    }

    func parse_unary() -> Int64 {
        if self.match("MINUS") {
            var child: Int64 = __pytra_int(self.parse_unary())
            return self.add_expr(ExprNode("neg", Int64(0), "", "", child, (-Int64(1))))
        }
        return self.parse_primary()
    }

    func parse_primary() -> Int64 {
        if self.match("NUMBER") {
            var token_num: Token = ((__pytra_getIndex(self.tokens, (__pytra_int(self.pos) - __pytra_int(Int64(1)))) as? Token) ?? Token() as? Token) ?? Token()
            return self.add_expr(ExprNode("lit", __pytra_int(token_num.text), "", "", (-Int64(1)), (-Int64(1))))
        }
        if self.match("IDENT") {
            var token_ident: Token = ((__pytra_getIndex(self.tokens, (__pytra_int(self.pos) - __pytra_int(Int64(1)))) as? Token) ?? Token() as? Token) ?? Token()
            return self.add_expr(ExprNode("var", Int64(0), token_ident.text, "", (-Int64(1)), (-Int64(1))))
        }
        if self.match("LPAREN") {
            var expr_index: Int64 = __pytra_int(self.parse_expr())
            self.expect("RPAREN")
            return expr_index
        }
        var t: Token = ((__pytra_getIndex(self.tokens, self.pos) as? Token) ?? Token() as? Token) ?? Token()
        fatalError("pytra raise")
        return 0
    }
}

func tokenize(lines: [Any]) -> [Any] {
    var tokens: [Any] = __pytra_as_list([])
    // TODO: unsupported ForCore plan
    tokens = __pytra_as_list(tokens); tokens.append(Token("EOF", "", __pytra_len(lines)))
    return tokens
}

func eval_expr(expr_index: Int64, expr_nodes: [Any], env: [AnyHashable: Any]) -> Int64 {
    var node: ExprNode = ((__pytra_getIndex(expr_nodes, expr_index) as? ExprNode) ?? ExprNode() as? ExprNode) ?? ExprNode()
    if (__pytra_str(node.kind) == __pytra_str("lit")) {
        return node.value
    }
    if (__pytra_str(node.kind) == __pytra_str("var")) {
        if (!(__pytra_contains(env, node.name))) {
            fatalError("pytra raise")
        }
        return __pytra_int(__pytra_getIndex(env, node.name))
    }
    if (__pytra_str(node.kind) == __pytra_str("neg")) {
        return (-eval_expr(node.left, expr_nodes, env))
    }
    if (__pytra_str(node.kind) == __pytra_str("bin")) {
        var lhs: Int64 = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs: Int64 = __pytra_int(eval_expr(node.right, expr_nodes, env))
        if (__pytra_str(node.op) == __pytra_str("+")) {
            return (__pytra_int(lhs) + __pytra_int(rhs))
        }
        if (__pytra_str(node.op) == __pytra_str("-")) {
            return (__pytra_int(lhs) - __pytra_int(rhs))
        }
        if (__pytra_str(node.op) == __pytra_str("*")) {
            return (__pytra_int(lhs) * __pytra_int(rhs))
        }
        if (__pytra_str(node.op) == __pytra_str("/")) {
            if (__pytra_int(rhs) == __pytra_int(Int64(0))) {
                fatalError("pytra raise")
            }
            return (__pytra_int(__pytra_int(lhs) / __pytra_int(rhs)))
        }
        fatalError("pytra raise")
    }
    fatalError("pytra raise")
    return 0
}

func execute(stmts: [Any], expr_nodes: [Any], trace: Bool) -> Int64 {
    var env: [AnyHashable: Any] = __pytra_as_dict([:])
    var checksum: Int64 = __pytra_int(Int64(0))
    var printed: Int64 = __pytra_int(Int64(0))
    let __iter_0 = __pytra_as_list(stmts)
    var __i_1: Int64 = 0
    while __i_1 < Int64(__iter_0.count) {
        let stmt = __iter_0[Int(__i_1)]
        if (__pytra_str(stmt.kind) == __pytra_str("let")) {
            __pytra_setIndex(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        if (__pytra_str(stmt.kind) == __pytra_str("assign")) {
            if (!(__pytra_contains(env, stmt.name))) {
                fatalError("pytra raise")
            }
            __pytra_setIndex(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        var value: Int64 = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
        if trace {
            __pytra_print(value)
        }
        var norm: Int64 = __pytra_int((__pytra_int(value) % __pytra_int(Int64(1000000007))))
        if (__pytra_int(norm) < __pytra_int(Int64(0))) {
            norm += Int64(1000000007)
        }
        checksum = __pytra_int((__pytra_int((__pytra_int((__pytra_int(checksum) * __pytra_int(Int64(131)))) + __pytra_int(norm))) % __pytra_int(Int64(1000000007))))
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
    let __step_0 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_0 >= 0 && i < __pytra_int(var_count)) || (__step_0 < 0 && i > __pytra_int(var_count))) {
        lines = __pytra_as_list(lines); lines.append((__pytra_str((__pytra_str((__pytra_str("let v") + __pytra_str(__pytra_str(i)))) + __pytra_str(" = "))) + __pytra_str(__pytra_str((__pytra_int(i) + __pytra_int(Int64(1)))))))
        i += __step_0
    }
    let __step_1 = __pytra_int(Int64(1))
    var i = __pytra_int(Int64(0))
    while ((__step_1 >= 0 && i < __pytra_int(loops)) || (__step_1 < 0 && i > __pytra_int(loops))) {
        var x: Int64 = __pytra_int((__pytra_int(i) % __pytra_int(var_count)))
        var y: Int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(Int64(3)))) % __pytra_int(var_count)))
        var c1: Int64 = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(Int64(7)))) + __pytra_int(Int64(1))))
        var c2: Int64 = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(Int64(11)))) + __pytra_int(Int64(2))))
        lines = __pytra_as_list(lines); lines.append((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("v") + __pytra_str(__pytra_str(x)))) + __pytra_str(" = (v"))) + __pytra_str(__pytra_str(x)))) + __pytra_str(" * "))) + __pytra_str(__pytra_str(c1)))) + __pytra_str(" + v"))) + __pytra_str(__pytra_str(y)))) + __pytra_str(" + 10000) / "))) + __pytra_str(__pytra_str(c2))))
        if (__pytra_int((__pytra_int(i) % __pytra_int(Int64(97)))) == __pytra_int(Int64(0))) {
            lines = __pytra_as_list(lines); lines.append((__pytra_str("print v") + __pytra_str(__pytra_str(x))))
        }
        i += __step_1
    }
    lines = __pytra_as_list(lines); lines.append("print (v0 + v1 + v2 + v3)")
    return lines
}

func run_demo() {
    var demo_lines: [Any] = __pytra_as_list([])
    demo_lines = __pytra_as_list(demo_lines); demo_lines.append("let a = 10")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.append("let b = 3")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.append("a = (a + b) * 2")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.append("print a")
    demo_lines = __pytra_as_list(demo_lines); demo_lines.append("print a / b")
    var tokens: [Any] = __pytra_as_list(tokenize(demo_lines))
    var parser: Parser = (Parser(tokens) as? Parser) ?? Parser()
    var stmts: [Any] = __pytra_as_list(parser.parse_program())
    var checksum: Int64 = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

func run_benchmark() {
    var source_lines: [Any] = __pytra_as_list(build_benchmark_source(Int64(32), Int64(120000)))
    var start: Double = __pytra_float(__pytra_perf_counter())
    var tokens: [Any] = __pytra_as_list(tokenize(source_lines))
    var parser: Parser = (Parser(tokens) as? Parser) ?? Parser()
    var stmts: [Any] = __pytra_as_list(parser.parse_program())
    var checksum: Int64 = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed: Double = __pytra_float((__pytra_perf_counter() - start))
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
