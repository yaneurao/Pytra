// Auto-generated Pytra Go native source from EAST3.
package main

import (
    "fmt"
    "math"
    "strconv"
    "time"
    "unicode"
)

var _ = math.Pi

func __pytra_noop(args ...any) {}

func __pytra_assert(args ...any) string {
    _ = args
    return "True"
}

func __pytra_perf_counter() float64 {
    return float64(time.Now().UnixNano()) / 1_000_000_000.0
}

func __pytra_truthy(v any) bool {
    switch t := v.(type) {
    case nil:
        return false
    case bool:
        return t
    case int:
        return t != 0
    case int64:
        return t != 0
    case float64:
        return t != 0.0
    case string:
        return t != ""
    case []any:
        return len(t) != 0
    case map[any]any:
        return len(t) != 0
    default:
        return true
    }
}

func __pytra_int(v any) int64 {
    switch t := v.(type) {
    case nil:
        return 0
    case int:
        return int64(t)
    case int64:
        return t
    case float64:
        return int64(t)
    case bool:
        if t {
            return 1
        }
        return 0
    case string:
        if t == "" {
            return 0
        }
        n, err := strconv.ParseInt(t, 10, 64)
        if err != nil {
            return 0
        }
        return n
    default:
        return 0
    }
}

func __pytra_float(v any) float64 {
    switch t := v.(type) {
    case nil:
        return 0.0
    case int:
        return float64(t)
    case int64:
        return float64(t)
    case float64:
        return t
    case bool:
        if t {
            return 1.0
        }
        return 0.0
    case string:
        if t == "" {
            return 0.0
        }
        n, err := strconv.ParseFloat(t, 64)
        if err != nil {
            return 0.0
        }
        return n
    default:
        return 0.0
    }
}

func __pytra_str(v any) string {
    if v == nil {
        return ""
    }
    switch t := v.(type) {
    case string:
        return t
    default:
        return fmt.Sprint(v)
    }
}

func __pytra_len(v any) int64 {
    switch t := v.(type) {
    case nil:
        return 0
    case string:
        return int64(len([]rune(t)))
    case []any:
        return int64(len(t))
    case map[any]any:
        return int64(len(t))
    default:
        return 0
    }
}

func __pytra_index(i int64, n int64) int64 {
    if i < 0 {
        i += n
    }
    return i
}

func __pytra_get_index(container any, index any) any {
    switch t := container.(type) {
    case []any:
        if len(t) == 0 {
            return nil
        }
        i := __pytra_index(__pytra_int(index), int64(len(t)))
        if i < 0 || i >= int64(len(t)) {
            return nil
        }
        return t[i]
    case map[any]any:
        return t[index]
    case string:
        runes := []rune(t)
        if len(runes) == 0 {
            return ""
        }
        i := __pytra_index(__pytra_int(index), int64(len(runes)))
        if i < 0 || i >= int64(len(runes)) {
            return ""
        }
        return string(runes[i])
    default:
        return nil
    }
}

func __pytra_set_index(container any, index any, value any) {
    switch t := container.(type) {
    case []any:
        if len(t) == 0 {
            return
        }
        i := __pytra_index(__pytra_int(index), int64(len(t)))
        if i < 0 || i >= int64(len(t)) {
            return
        }
        t[i] = value
    case map[any]any:
        t[index] = value
    }
}

func __pytra_slice(container any, lower any, upper any) any {
    switch t := container.(type) {
    case string:
        runes := []rune(t)
        n := int64(len(runes))
        lo := __pytra_index(__pytra_int(lower), n)
        hi := __pytra_index(__pytra_int(upper), n)
        if lo < 0 {
            lo = 0
        }
        if hi < 0 {
            hi = 0
        }
        if lo > n {
            lo = n
        }
        if hi > n {
            hi = n
        }
        if hi < lo {
            hi = lo
        }
        return string(runes[lo:hi])
    case []any:
        n := int64(len(t))
        lo := __pytra_index(__pytra_int(lower), n)
        hi := __pytra_index(__pytra_int(upper), n)
        if lo < 0 {
            lo = 0
        }
        if hi < 0 {
            hi = 0
        }
        if lo > n {
            lo = n
        }
        if hi > n {
            hi = n
        }
        if hi < lo {
            hi = lo
        }
        out := []any{}
        i := lo
        for i < hi {
            out = append(out, t[i])
            i += 1
        }
        return out
    default:
        return nil
    }
}

func __pytra_isdigit(v any) bool {
    s := __pytra_str(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !unicode.IsDigit(ch) {
            return false
        }
    }
    return true
}

func __pytra_isalpha(v any) bool {
    s := __pytra_str(v)
    if s == "" {
        return false
    }
    for _, ch := range s {
        if !unicode.IsLetter(ch) {
            return false
        }
    }
    return true
}

func __pytra_contains(container any, value any) bool {
    switch t := container.(type) {
    case []any:
        i := 0
        for i < len(t) {
            if t[i] == value {
                return true
            }
            i += 1
        }
        return false
    case map[any]any:
        _, ok := t[value]
        return ok
    case string:
        needle := __pytra_str(value)
        return needle != "" && len(needle) <= len(t) && __pytra_str_contains(t, needle)
    default:
        return false
    }
}

func __pytra_str_contains(haystack string, needle string) bool {
    if needle == "" {
        return true
    }
    i := 0
    limit := len(haystack) - len(needle)
    for i <= limit {
        if haystack[i:i+len(needle)] == needle {
            return true
        }
        i += 1
    }
    return false
}

func __pytra_ifexp(cond bool, a any, b any) any {
    if cond {
        return a
    }
    return b
}

func __pytra_bytearray(init any) []any {
    out := []any{}
    switch t := init.(type) {
    case int:
        i := 0
        for i < t {
            out = append(out, int64(0))
            i += 1
        }
    case int64:
        i := int64(0)
        for i < t {
            out = append(out, int64(0))
            i += 1
        }
    case []any:
        i := 0
        for i < len(t) {
            out = append(out, t[i])
            i += 1
        }
    }
    return out
}

func __pytra_bytes(v any) []any {
    switch t := v.(type) {
    case []any:
        out := []any{}
        i := 0
        for i < len(t) {
            out = append(out, t[i])
            i += 1
        }
        return out
    default:
        return []any{}
    }
}

func __pytra_list_repeat(value any, count any) []any {
    out := []any{}
    n := __pytra_int(count)
    i := int64(0)
    for i < n {
        out = append(out, value)
        i += 1
    }
    return out
}

func __pytra_as_list(v any) []any {
    if t, ok := v.([]any); ok {
        return t
    }
    return []any{}
}

func __pytra_as_dict(v any) map[any]any {
    if t, ok := v.(map[any]any); ok {
        return t
    }
    return map[any]any{}
}

func __pytra_pop_last(v []any) []any {
    if len(v) == 0 {
        return v
    }
    return v[:len(v)-1]
}

func __pytra_print(args ...any) {
    if len(args) == 0 {
        fmt.Println()
        return
    }
    fmt.Println(args...)
}

func __pytra_min(a any, b any) any {
    af := __pytra_float(a)
    bf := __pytra_float(b)
    if af < bf {
        if __pytra_is_float(a) || __pytra_is_float(b) {
            return af
        }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) {
        return bf
    }
    return __pytra_int(b)
}

func __pytra_max(a any, b any) any {
    af := __pytra_float(a)
    bf := __pytra_float(b)
    if af > bf {
        if __pytra_is_float(a) || __pytra_is_float(b) {
            return af
        }
        return __pytra_int(a)
    }
    if __pytra_is_float(a) || __pytra_is_float(b) {
        return bf
    }
    return __pytra_int(b)
}

func __pytra_is_int(v any) bool {
    switch v.(type) {
    case int, int64:
        return true
    default:
        return false
    }
}

func __pytra_is_float(v any) bool {
    _, ok := v.(float64)
    return ok
}

func __pytra_is_bool(v any) bool {
    _, ok := v.(bool)
    return ok
}

func __pytra_is_str(v any) bool {
    _, ok := v.(string)
    return ok
}

func __pytra_is_list(v any) bool {
    _, ok := v.([]any)
    return ok
}

func __pytra_is_Token(v any) bool {
    _, ok := v.(*Token)
    return ok
}

func __pytra_is_ExprNode(v any) bool {
    _, ok := v.(*ExprNode)
    return ok
}

func __pytra_is_StmtNode(v any) bool {
    _, ok := v.(*StmtNode)
    return ok
}

func __pytra_is_Parser(v any) bool {
    _, ok := v.(*Parser)
    return ok
}

type Token struct {
    kind string
    text string
    pos int64
}

func NewToken() *Token {
    self := &Token{}
    return self
}

type ExprNode struct {
    kind string
    value int64
    name string
    op string
    left int64
    right int64
}

func NewExprNode() *ExprNode {
    self := &ExprNode{}
    return self
}

type StmtNode struct {
    kind string
    name string
    expr_index int64
}

func NewStmtNode() *StmtNode {
    self := &StmtNode{}
    return self
}

type Parser struct {
    tokens []any
    pos int64
    expr_nodes []any
}

func NewParser(tokens []any) *Parser {
    self := &Parser{}
    self.Init(tokens)
    return self
}

func (self *Parser) new_expr_nodes() []any {
    return []any{}
}

func (self *Parser) Init(tokens []any) {
    self.tokens = tokens
    self.pos = int64(0)
    self.expr_nodes = self.new_expr_nodes()
}

func (self *Parser) peek_kind() string {
    return __pytra_get_index(self.tokens, self.pos).kind
}

func (self *Parser) match(kind string) bool {
    if (__pytra_str(self.peek_kind()) == __pytra_str(kind)) {
        self.pos += int64(1)
        return true
    }
    return false
}

func (self *Parser) expect(kind string) *Token {
    if (__pytra_str(self.peek_kind()) != __pytra_str(kind)) {
        var t *Token = __pytra_get_index(self.tokens, self.pos)
        panic("pytra raise")
    }
    var token *Token = __pytra_get_index(self.tokens, self.pos)
    self.pos += int64(1)
    return token
}

func (self *Parser) skip_newlines() {
    for self.match("NEWLINE") {
        // pass
    }
}

func (self *Parser) add_expr(node *ExprNode) int64 {
    self.expr_nodes = append(__pytra_as_list(self.expr_nodes), node)
    return (__pytra_int(__pytra_len(self.expr_nodes)) - __pytra_int(int64(1)))
}

func (self *Parser) parse_program() []any {
    var stmts []any = __pytra_as_list([]any{})
    self.skip_newlines()
    for (__pytra_str(self.peek_kind()) != __pytra_str("EOF")) {
        var stmt *StmtNode = self.parse_stmt()
        stmts = append(__pytra_as_list(stmts), stmt)
        self.skip_newlines()
    }
    return stmts
}

func (self *Parser) parse_stmt() *StmtNode {
    if self.match("LET") {
        var let_name string = __pytra_str(self.expect("IDENT").text)
        self.expect("EQUAL")
        var let_expr_index int64 = __pytra_int(self.parse_expr())
        return NewStmtNode("let", let_name, let_expr_index)
    }
    if self.match("PRINT") {
        var print_expr_index int64 = __pytra_int(self.parse_expr())
        return NewStmtNode("print", "", print_expr_index)
    }
    var assign_name string = __pytra_str(self.expect("IDENT").text)
    self.expect("EQUAL")
    var assign_expr_index int64 = __pytra_int(self.parse_expr())
    return NewStmtNode("assign", assign_name, assign_expr_index)
}

func (self *Parser) parse_expr() int64 {
    return self.parse_add()
}

func (self *Parser) parse_add() int64 {
    var left int64 = __pytra_int(self.parse_mul())
    for true {
        if self.match("PLUS") {
            var right int64 = __pytra_int(self.parse_mul())
            left = __pytra_int(self.add_expr(NewExprNode("bin", int64(0), "", "+", left, right)))
            continue
        }
        if self.match("MINUS") {
            var right int64 = __pytra_int(self.parse_mul())
            left = __pytra_int(self.add_expr(NewExprNode("bin", int64(0), "", "-", left, right)))
            continue
        }
        break
    }
    return left
}

func (self *Parser) parse_mul() int64 {
    var left int64 = __pytra_int(self.parse_unary())
    for true {
        if self.match("STAR") {
            var right int64 = __pytra_int(self.parse_unary())
            left = __pytra_int(self.add_expr(NewExprNode("bin", int64(0), "", "*", left, right)))
            continue
        }
        if self.match("SLASH") {
            var right int64 = __pytra_int(self.parse_unary())
            left = __pytra_int(self.add_expr(NewExprNode("bin", int64(0), "", "/", left, right)))
            continue
        }
        break
    }
    return left
}

func (self *Parser) parse_unary() int64 {
    if self.match("MINUS") {
        var child int64 = __pytra_int(self.parse_unary())
        return self.add_expr(NewExprNode("neg", int64(0), "", "", child, (-int64(1))))
    }
    return self.parse_primary()
}

func (self *Parser) parse_primary() int64 {
    if self.match("NUMBER") {
        var token_num *Token = __pytra_get_index(self.tokens, (__pytra_int(self.pos) - __pytra_int(int64(1))))
        return self.add_expr(NewExprNode("lit", __pytra_int(token_num.text), "", "", (-int64(1)), (-int64(1))))
    }
    if self.match("IDENT") {
        var token_ident *Token = __pytra_get_index(self.tokens, (__pytra_int(self.pos) - __pytra_int(int64(1))))
        return self.add_expr(NewExprNode("var", int64(0), token_ident.text, "", (-int64(1)), (-int64(1))))
    }
    if self.match("LPAREN") {
        var expr_index int64 = __pytra_int(self.parse_expr())
        self.expect("RPAREN")
        return expr_index
    }
    var t *Token = __pytra_get_index(self.tokens, self.pos)
    panic("pytra raise")
    return 0
}

func tokenize(lines []any) []any {
    var tokens []any = __pytra_as_list([]any{})
    // TODO: unsupported ForCore plan
    tokens = append(__pytra_as_list(tokens), NewToken("EOF", "", __pytra_len(lines)))
    return tokens
}

func eval_expr(expr_index int64, expr_nodes []any, env map[any]any) int64 {
    var node *ExprNode = __pytra_get_index(expr_nodes, expr_index)
    if (__pytra_str(node.kind) == __pytra_str("lit")) {
        return node.value
    }
    if (__pytra_str(node.kind) == __pytra_str("var")) {
        if (!(__pytra_contains(env, node.name))) {
            panic("pytra raise")
        }
        return __pytra_int(__pytra_get_index(env, node.name))
    }
    if (__pytra_str(node.kind) == __pytra_str("neg")) {
        return (-eval_expr(node.left, expr_nodes, env))
    }
    if (__pytra_str(node.kind) == __pytra_str("bin")) {
        var lhs int64 = __pytra_int(eval_expr(node.left, expr_nodes, env))
        var rhs int64 = __pytra_int(eval_expr(node.right, expr_nodes, env))
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
            if (__pytra_int(rhs) == __pytra_int(int64(0))) {
                panic("pytra raise")
            }
            return (__pytra_int(__pytra_int(lhs) / __pytra_int(rhs)))
        }
        panic("pytra raise")
    }
    panic("pytra raise")
    return 0
}

func execute(stmts []any, expr_nodes []any, trace bool) int64 {
    var env map[any]any = __pytra_as_dict(map[any]any{})
    var checksum int64 = __pytra_int(int64(0))
    var printed int64 = __pytra_int(int64(0))
    __iter_0 := __pytra_as_list(stmts)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        stmt := __iter_0[__i_1]
        if (__pytra_str(stmt.kind) == __pytra_str("let")) {
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        if (__pytra_str(stmt.kind) == __pytra_str("assign")) {
            if (!(__pytra_contains(env, stmt.name))) {
                panic("pytra raise")
            }
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        var value int64 = __pytra_int(eval_expr(stmt.expr_index, expr_nodes, env))
        if trace {
            __pytra_print(value)
        }
        var norm int64 = __pytra_int((__pytra_int(value) % __pytra_int(int64(1000000007))))
        if (__pytra_int(norm) < __pytra_int(int64(0))) {
            norm += int64(1000000007)
        }
        checksum = __pytra_int((__pytra_int((__pytra_int((__pytra_int(checksum) * __pytra_int(int64(131)))) + __pytra_int(norm))) % __pytra_int(int64(1000000007))))
        printed += int64(1)
    }
    if trace {
        __pytra_print("printed:", printed)
    }
    return checksum
}

func build_benchmark_source(var_count int64, loops int64) []any {
    var lines []any = __pytra_as_list([]any{})
    __step_0 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_0 >= 0 && i < __pytra_int(var_count)) || (__step_0 < 0 && i > __pytra_int(var_count)); i += __step_0 {
        lines = append(__pytra_as_list(lines), (__pytra_str((__pytra_str((__pytra_str("let v") + __pytra_str(__pytra_str(i)))) + __pytra_str(" = "))) + __pytra_str(__pytra_str((__pytra_int(i) + __pytra_int(int64(1)))))))
    }
    __step_1 := __pytra_int(int64(1))
    for i := __pytra_int(int64(0)); (__step_1 >= 0 && i < __pytra_int(loops)) || (__step_1 < 0 && i > __pytra_int(loops)); i += __step_1 {
        var x int64 = __pytra_int((__pytra_int(i) % __pytra_int(var_count)))
        var y int64 = __pytra_int((__pytra_int((__pytra_int(i) + __pytra_int(int64(3)))) % __pytra_int(var_count)))
        var c1 int64 = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(int64(7)))) + __pytra_int(int64(1))))
        var c2 int64 = __pytra_int((__pytra_int((__pytra_int(i) % __pytra_int(int64(11)))) + __pytra_int(int64(2))))
        lines = append(__pytra_as_list(lines), (__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("v") + __pytra_str(__pytra_str(x)))) + __pytra_str(" = (v"))) + __pytra_str(__pytra_str(x)))) + __pytra_str(" * "))) + __pytra_str(__pytra_str(c1)))) + __pytra_str(" + v"))) + __pytra_str(__pytra_str(y)))) + __pytra_str(" + 10000) / "))) + __pytra_str(__pytra_str(c2))))
        if (__pytra_int((__pytra_int(i) % __pytra_int(int64(97)))) == __pytra_int(int64(0))) {
            lines = append(__pytra_as_list(lines), (__pytra_str("print v") + __pytra_str(__pytra_str(x))))
        }
    }
    lines = append(__pytra_as_list(lines), "print (v0 + v1 + v2 + v3)")
    return lines
}

func run_demo() {
    var demo_lines []any = __pytra_as_list([]any{})
    demo_lines = append(__pytra_as_list(demo_lines), "let a = 10")
    demo_lines = append(__pytra_as_list(demo_lines), "let b = 3")
    demo_lines = append(__pytra_as_list(demo_lines), "a = (a + b) * 2")
    demo_lines = append(__pytra_as_list(demo_lines), "print a")
    demo_lines = append(__pytra_as_list(demo_lines), "print a / b")
    var tokens []any = __pytra_as_list(tokenize(demo_lines))
    var parser *Parser = NewParser(tokens)
    var stmts []any = __pytra_as_list(parser.parse_program())
    var checksum int64 = __pytra_int(execute(stmts, parser.expr_nodes, true))
    __pytra_print("demo_checksum:", checksum)
}

func run_benchmark() {
    var source_lines []any = __pytra_as_list(build_benchmark_source(int64(32), int64(120000)))
    var start float64 = __pytra_float(__pytra_perf_counter())
    var tokens []any = __pytra_as_list(tokenize(source_lines))
    var parser *Parser = NewParser(tokens)
    var stmts []any = __pytra_as_list(parser.parse_program())
    var checksum int64 = __pytra_int(execute(stmts, parser.expr_nodes, false))
    var elapsed float64 = __pytra_float((__pytra_perf_counter() - start))
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

func main() {
    main()
}
