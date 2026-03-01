package main

type TokenLike interface {
}

type ExprNodeLike interface {
}

type StmtNodeLike interface {
}

type ParserLike interface {
    new_expr_nodes() []any
    current_token() TokenLike
    previous_token() TokenLike
    peek_kind() string
    match(kind string) bool
    expect(kind string) TokenLike
    skip_newlines()
    add_expr(node ExprNodeLike) int64
    parse_program() []any
    parse_stmt() StmtNodeLike
    parse_expr() int64
    parse_add() int64
    parse_mul() int64
    parse_unary() int64
    parse_primary() int64
}


func __pytra_is_Token(v any) bool {
    _, ok := v.(*Token)
    return ok
}

func __pytra_as_Token(v any) *Token {
    if t, ok := v.(*Token); ok {
        return t
    }
    return nil
}

func __pytra_is_ExprNode(v any) bool {
    _, ok := v.(*ExprNode)
    return ok
}

func __pytra_as_ExprNode(v any) *ExprNode {
    if t, ok := v.(*ExprNode); ok {
        return t
    }
    return nil
}

func __pytra_is_StmtNode(v any) bool {
    _, ok := v.(*StmtNode)
    return ok
}

func __pytra_as_StmtNode(v any) *StmtNode {
    if t, ok := v.(*StmtNode); ok {
        return t
    }
    return nil
}

func __pytra_is_Parser(v any) bool {
    _, ok := v.(*Parser)
    return ok
}

func __pytra_as_Parser(v any) *Parser {
    if t, ok := v.(*Parser); ok {
        return t
    }
    return nil
}

type Token struct {
    kind string
    text string
    pos int64
    number_value int64
}

func NewToken(kind string, text string, pos int64, number_value int64) *Token {
    self := &Token{}
    self.kind = kind
    self.text = text
    self.pos = pos
    self.number_value = number_value
    return self
}

type ExprNode struct {
    kind string
    value int64
    name string
    op string
    left int64
    right int64
    kind_tag int64
    op_tag int64
}

func NewExprNode(kind string, value int64, name string, op string, left int64, right int64, kind_tag int64, op_tag int64) *ExprNode {
    self := &ExprNode{}
    self.kind = kind
    self.value = value
    self.name = name
    self.op = op
    self.left = left
    self.right = right
    self.kind_tag = kind_tag
    self.op_tag = op_tag
    return self
}

type StmtNode struct {
    kind string
    name string
    expr_index int64
    kind_tag int64
}

func NewStmtNode(kind string, name string, expr_index int64, kind_tag int64) *StmtNode {
    self := &StmtNode{}
    self.kind = kind
    self.name = name
    self.expr_index = expr_index
    self.kind_tag = kind_tag
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
    return __pytra_as_list([]any{})
}

func (self *Parser) Init(tokens []any) {
    self.tokens = tokens
    self.pos = int64(0)
    self.expr_nodes = self.new_expr_nodes()
}

func (self *Parser) current_token() TokenLike {
    return __pytra_get_index(self.tokens, self.pos)
}

func (self *Parser) previous_token() TokenLike {
    return __pytra_get_index(self.tokens, (self.pos - int64(1)))
}

func (self *Parser) peek_kind() string {
    return __pytra_str(self.current_token().kind)
}

func (self *Parser) match(kind string) bool {
    if (__pytra_str(self.peek_kind()) == __pytra_str(kind)) {
        self.pos += int64(1)
        return __pytra_truthy(true)
    }
    return __pytra_truthy(false)
}

func (self *Parser) expect(kind string) TokenLike {
    var token TokenLike = self.current_token()
    if (__pytra_str(token.kind) != __pytra_str(kind)) {
        panic(__pytra_str(((__pytra_str((__pytra_str((__pytra_str((__pytra_str("parse error at pos=") + __pytra_str(__pytra_str(token.pos)))) + __pytra_str(", expected="))) + __pytra_str(kind))) + __pytra_str(", got=")) + token.kind)))
    }
    self.pos += int64(1)
    return token
}

func (self *Parser) skip_newlines() {
    for self.match("NEWLINE") {
        _ = 0
    }
}

func (self *Parser) add_expr(node ExprNodeLike) int64 {
    self.expr_nodes = append(__pytra_as_list(self.expr_nodes), node)
    return (__pytra_len(self.expr_nodes) - int64(1))
}

func (self *Parser) parse_program() []any {
    var stmts []any = __pytra_as_list([]any{})
    self.skip_newlines()
    for (__pytra_str(self.peek_kind()) != __pytra_str("EOF")) {
        var stmt StmtNodeLike = self.parse_stmt()
        stmts = append(__pytra_as_list(stmts), stmt)
        self.skip_newlines()
    }
    return __pytra_as_list(stmts)
}

func (self *Parser) parse_stmt() StmtNodeLike {
    if self.match("LET") {
        var let_name string = __pytra_str(self.expect("IDENT").text)
        self.expect("EQUAL")
        var let_expr_index int64 = self.parse_expr()
        return NewStmtNode("let", let_name, let_expr_index, int64(1))
    }
    if self.match("PRINT") {
        var print_expr_index int64 = self.parse_expr()
        return NewStmtNode("print", "", print_expr_index, int64(3))
    }
    var assign_name string = __pytra_str(self.expect("IDENT").text)
    self.expect("EQUAL")
    var assign_expr_index int64 = self.parse_expr()
    return NewStmtNode("assign", assign_name, assign_expr_index, int64(2))
}

func (self *Parser) parse_expr() int64 {
    return self.parse_add()
}

func (self *Parser) parse_add() int64 {
    var left int64 = self.parse_mul()
    for true {
        if self.match("PLUS") {
            var right int64 = self.parse_mul()
            left = self.add_expr(NewExprNode("bin", int64(0), "", "+", left, right, int64(3), int64(1)))
            continue
        }
        if self.match("MINUS") {
            var right int64 = self.parse_mul()
            left = self.add_expr(NewExprNode("bin", int64(0), "", "-", left, right, int64(3), int64(2)))
            continue
        }
        break
    }
    return left
}

func (self *Parser) parse_mul() int64 {
    var left int64 = self.parse_unary()
    for true {
        if self.match("STAR") {
            var right int64 = self.parse_unary()
            left = self.add_expr(NewExprNode("bin", int64(0), "", "*", left, right, int64(3), int64(3)))
            continue
        }
        if self.match("SLASH") {
            var right int64 = self.parse_unary()
            left = self.add_expr(NewExprNode("bin", int64(0), "", "/", left, right, int64(3), int64(4)))
            continue
        }
        break
    }
    return left
}

func (self *Parser) parse_unary() int64 {
    if self.match("MINUS") {
        var child int64 = self.parse_unary()
        return self.add_expr(NewExprNode("neg", int64(0), "", "", child, (-int64(1)), int64(4), int64(0)))
    }
    return self.parse_primary()
}

func (self *Parser) parse_primary() int64 {
    if self.match("NUMBER") {
        var token_num TokenLike = self.previous_token()
        return self.add_expr(NewExprNode("lit", token_num.number_value, "", "", (-int64(1)), (-int64(1)), int64(1), int64(0)))
    }
    if self.match("IDENT") {
        var token_ident TokenLike = self.previous_token()
        return self.add_expr(NewExprNode("var", int64(0), token_ident.text, "", (-int64(1)), (-int64(1)), int64(2), int64(0)))
    }
    if self.match("LPAREN") {
        var expr_index int64 = self.parse_expr()
        self.expect("RPAREN")
        return expr_index
    }
    var t TokenLike = self.current_token()
    panic(__pytra_str(((__pytra_str((__pytra_str("primary parse error at pos=") + __pytra_str(__pytra_str(t.pos)))) + __pytra_str(" got=")) + t.kind)))
    return 0
}

func tokenize(lines []any) []any {
    var single_char_token_tags map[any]any = __pytra_as_dict(map[any]any{})
    var single_char_token_kinds []any = __pytra_as_list([]any{"PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"})
    var tokens []any = __pytra_as_list([]any{})
    __iter_0 := __pytra_as_list(__pytra_enumerate(lines))
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        __it_2 := __iter_0[__i_1]
        __tuple_3 := __pytra_as_list(__it_2)
        var line_index int64 = __pytra_int(__tuple_3[0])
        _ = line_index
        var source string = __pytra_str(__tuple_3[1])
        _ = source
        var i int64 = int64(0)
        var n int64 = __pytra_len(source)
        for (i < n) {
            var ch string = __pytra_str(__pytra_str(__pytra_get_index(source, i)))
            if (__pytra_str(ch) == __pytra_str(" ")) {
                i += int64(1)
                continue
            }
            var single_tag int64 = single_char_token_tags.get(ch, int64(0))
            if (single_tag > int64(0)) {
                tokens = append(__pytra_as_list(tokens), NewToken(__pytra_str(__pytra_get_index(single_char_token_kinds, (single_tag - int64(1)))), ch, i, int64(0)))
                i += int64(1)
                continue
            }
            if __pytra_truthy(__pytra_isdigit(ch)) {
                var start int64 = i
                for ((i < n) && __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i))))) {
                    i += int64(1)
                }
                var text string = __pytra_str(__pytra_slice(source, start, i))
                tokens = append(__pytra_as_list(tokens), NewToken("NUMBER", text, start, __pytra_int(text)))
                continue
            }
            if (__pytra_truthy(__pytra_isalpha(ch)) || (__pytra_str(ch) == __pytra_str("_"))) {
                var start int64 = i
                for ((i < n) && ((__pytra_truthy(__pytra_isalpha(__pytra_str(__pytra_get_index(source, i)))) || (__pytra_str(__pytra_str(__pytra_get_index(source, i))) == __pytra_str("_"))) || __pytra_truthy(__pytra_isdigit(__pytra_str(__pytra_get_index(source, i)))))) {
                    i += int64(1)
                }
                var text string = __pytra_str(__pytra_slice(source, start, i))
                if (__pytra_str(text) == __pytra_str("let")) {
                    tokens = append(__pytra_as_list(tokens), NewToken("LET", text, start, int64(0)))
                } else {
                    if (__pytra_str(text) == __pytra_str("print")) {
                        tokens = append(__pytra_as_list(tokens), NewToken("PRINT", text, start, int64(0)))
                    } else {
                        tokens = append(__pytra_as_list(tokens), NewToken("IDENT", text, start, int64(0)))
                    }
                }
                continue
            }
            panic(__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("tokenize error at line=") + __pytra_str(__pytra_str(line_index)))) + __pytra_str(" pos="))) + __pytra_str(__pytra_str(i)))) + __pytra_str(" ch="))) + __pytra_str(ch))))
        }
        tokens = append(__pytra_as_list(tokens), NewToken("NEWLINE", "", n, int64(0)))
    }
    tokens = append(__pytra_as_list(tokens), NewToken("EOF", "", __pytra_len(lines), int64(0)))
    return __pytra_as_list(tokens)
}

func eval_expr(expr_index int64, expr_nodes []any, env map[any]any) int64 {
    var node ExprNodeLike = __pytra_get_index(expr_nodes, expr_index)
    if (__pytra_int(node.kind_tag) == int64(1)) {
        return __pytra_int(node.value)
    }
    if (__pytra_int(node.kind_tag) == int64(2)) {
        if (!(__pytra_contains(env, node.name))) {
            panic(__pytra_str(("undefined variable: " + node.name)))
        }
        return __pytra_int(__pytra_get_index(env, node.name))
    }
    if (__pytra_int(node.kind_tag) == int64(4)) {
        return (-eval_expr(node.left, expr_nodes, env))
    }
    if (__pytra_int(node.kind_tag) == int64(3)) {
        var lhs int64 = eval_expr(node.left, expr_nodes, env)
        var rhs int64 = eval_expr(node.right, expr_nodes, env)
        if (__pytra_int(node.op_tag) == int64(1)) {
            return (lhs + rhs)
        }
        if (__pytra_int(node.op_tag) == int64(2)) {
            return (lhs - rhs)
        }
        if (__pytra_int(node.op_tag) == int64(3)) {
            return (lhs * rhs)
        }
        if (__pytra_int(node.op_tag) == int64(4)) {
            if (rhs == int64(0)) {
                panic(__pytra_str("division by zero"))
            }
            return __pytra_int((lhs / rhs))
        }
        panic(__pytra_str(("unknown operator: " + node.op)))
    }
    panic(__pytra_str(("unknown node kind: " + node.kind)))
    return 0
}

func execute(stmts []any, expr_nodes []any, trace bool) int64 {
    var env map[any]any = __pytra_as_dict(map[any]any{})
    var checksum int64 = int64(0)
    var printed int64 = int64(0)
    __iter_0 := __pytra_as_list(stmts)
    for __i_1 := int64(0); __i_1 < int64(len(__iter_0)); __i_1 += 1 {
        var stmt StmtNodeLike = __iter_0[__i_1]
        if (__pytra_int(stmt.kind_tag) == int64(1)) {
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        if (__pytra_int(stmt.kind_tag) == int64(2)) {
            if (!(__pytra_contains(env, stmt.name))) {
                panic(__pytra_str(("assign to undefined variable: " + stmt.name)))
            }
            __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
            continue
        }
        var value int64 = eval_expr(stmt.expr_index, expr_nodes, env)
        if trace {
            __pytra_print(value)
        }
        var norm int64 = (value % int64(1000000007))
        if (norm < int64(0)) {
            norm += int64(1000000007)
        }
        checksum = (((checksum * int64(131)) + norm) % int64(1000000007))
        printed += int64(1)
    }
    if trace {
        __pytra_print("printed:", printed)
    }
    return checksum
}

func build_benchmark_source(var_count int64, loops int64) []any {
    var lines []any = __pytra_as_list([]any{})
    for i := int64(0); i < var_count; i += 1 {
        lines = append(__pytra_as_list(lines), (__pytra_str((__pytra_str((__pytra_str("let v") + __pytra_str(__pytra_str(i)))) + __pytra_str(" = "))) + __pytra_str(__pytra_str((i + int64(1))))))
    }
    for i := int64(0); i < loops; i += 1 {
        var x int64 = (i % var_count)
        var y int64 = ((i + int64(3)) % var_count)
        var c1 int64 = ((i % int64(7)) + int64(1))
        var c2 int64 = ((i % int64(11)) + int64(2))
        lines = append(__pytra_as_list(lines), (__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str((__pytra_str("v") + __pytra_str(__pytra_str(x)))) + __pytra_str(" = (v"))) + __pytra_str(__pytra_str(x)))) + __pytra_str(" * "))) + __pytra_str(__pytra_str(c1)))) + __pytra_str(" + v"))) + __pytra_str(__pytra_str(y)))) + __pytra_str(" + 10000) / "))) + __pytra_str(__pytra_str(c2))))
        if ((i % int64(97)) == int64(0)) {
            lines = append(__pytra_as_list(lines), (__pytra_str("print v") + __pytra_str(__pytra_str(x))))
        }
    }
    lines = append(__pytra_as_list(lines), "print (v0 + v1 + v2 + v3)")
    return __pytra_as_list(lines)
}

func run_demo() {
    var demo_lines []any = __pytra_as_list([]any{})
    demo_lines = append(__pytra_as_list(demo_lines), "let a = 10")
    demo_lines = append(__pytra_as_list(demo_lines), "let b = 3")
    demo_lines = append(__pytra_as_list(demo_lines), "a = (a + b) * 2")
    demo_lines = append(__pytra_as_list(demo_lines), "print a")
    demo_lines = append(__pytra_as_list(demo_lines), "print a / b")
    var tokens []any = __pytra_as_list(tokenize(demo_lines))
    var parser ParserLike = NewParser(tokens)
    var stmts []any = __pytra_as_list(parser.parse_program())
    var checksum int64 = execute(stmts, parser.expr_nodes, true)
    __pytra_print("demo_checksum:", checksum)
}

func run_benchmark() {
    var source_lines []any = __pytra_as_list(build_benchmark_source(int64(32), int64(120000)))
    var start float64 = __pytra_perf_counter()
    var tokens []any = __pytra_as_list(tokenize(source_lines))
    var parser ParserLike = NewParser(tokens)
    var stmts []any = __pytra_as_list(parser.parse_program())
    var checksum int64 = execute(stmts, parser.expr_nodes, false)
    var elapsed float64 = (__pytra_perf_counter() - start)
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
    __pytra_main()
}
