from dataclasses import dataclass
from time import perf_counter


# Tokens for lexical analysis.
@dataclass
class Token:
    kind: str
    text: str
    pos: int


# Expression node. `kind` identifies the concrete variant.
@dataclass
class ExprNode:
    kind: str        # "lit" | "var" | "bin" | "neg"
    value: int       # value for `lit`
    name: str        # name for `var`
    op: str          # operator for `bin`
    left: int        # child node index
    right: int       # child node index


# Statement node. `kind` identifies the concrete variant.
@dataclass
class StmtNode:
    kind: str        # "let" | "assign" | "print"
    name: str        # variable name (unused for `print`)
    expr_index: int  # expression node index

def tokenize(lines: list[str]) -> list[Token]:
    tokens: list[Token] = []
    for line_index, source in enumerate(lines):
        i: int = 0
        n: int = len(source)
        while i < n:
            ch: str = source[i]

            if ch == " ":
                i += 1
                continue

            if ch == "+":
                tokens.append(Token("PLUS", ch, i))
                i += 1
                continue

            if ch == "-":
                tokens.append(Token("MINUS", ch, i))
                i += 1
                continue

            if ch == "*":
                tokens.append(Token("STAR", ch, i))
                i += 1
                continue

            if ch == "/":
                tokens.append(Token("SLASH", ch, i))
                i += 1
                continue

            if ch == "(":
                tokens.append(Token("LPAREN", ch, i))
                i += 1
                continue

            if ch == ")":
                tokens.append(Token("RPAREN", ch, i))
                i += 1
                continue

            if ch == "=":
                tokens.append(Token("EQUAL", ch, i))
                i += 1
                continue

            if ch.isdigit():
                start: int = i
                while i < n and source[i].isdigit():
                    i += 1
                text: str = source[start:i]
                tokens.append(Token("NUMBER", text, start))
                continue

            if ch.isalpha() or ch == "_":
                start = i
                while i < n and ((source[i].isalpha() or source[i] == "_") or source[i].isdigit()):
                    i += 1
                text = source[start:i]
                if text == "let":
                    tokens.append(Token("LET", text, start))
                elif text == "print":
                    tokens.append(Token("PRINT", text, start))
                else:
                    tokens.append(Token("IDENT", text, start))
                continue

            raise RuntimeError("tokenize error at line=" + str(line_index) + " pos=" + str(i) + " ch=" + ch)

        tokens.append(Token("NEWLINE", "", n))

    tokens.append(Token("EOF", "", len(lines)))
    return tokens


class Parser:
    def new_expr_nodes(self) -> list[ExprNode]:
        nodes: list[ExprNode] = []
        return nodes

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens: list[Token] = tokens
        self.pos: int = 0
        self.expr_nodes: list[ExprNode] = self.new_expr_nodes()

    def peek_kind(self) -> str:
        return self.tokens[self.pos].kind

    def match(self, kind: str) -> bool:
        if self.peek_kind() == kind:
            self.pos += 1
            return True
        return False

    def expect(self, kind: str) -> Token:
        if self.peek_kind() != kind:
            t: Token = self.tokens[self.pos]
            raise RuntimeError("parse error at pos=" + str(t.pos) + ", expected=" + kind + ", got=" + t.kind)
        token: Token = self.tokens[self.pos]
        self.pos += 1
        return token

    def skip_newlines(self) -> None:
        while self.match("NEWLINE"):
            pass

    def add_expr(self, node: ExprNode) -> int:
        self.expr_nodes.append(node)
        return len(self.expr_nodes) - 1

    def parse_program(self) -> list[StmtNode]:
        stmts: list[StmtNode] = []
        self.skip_newlines()
        while self.peek_kind() != "EOF":
            stmt: StmtNode = self.parse_stmt()
            stmts.append(stmt)
            self.skip_newlines()
        return stmts

    def parse_stmt(self) -> StmtNode:
        if self.match("LET"):
            let_name: str = self.expect("IDENT").text
            self.expect("EQUAL")
            let_expr_index: int = self.parse_expr()
            return StmtNode("let", let_name, let_expr_index)

        if self.match("PRINT"):
            print_expr_index: int = self.parse_expr()
            return StmtNode("print", "", print_expr_index)

        assign_name: str = self.expect("IDENT").text
        self.expect("EQUAL")
        assign_expr_index: int = self.parse_expr()
        return StmtNode("assign", assign_name, assign_expr_index)

    def parse_expr(self) -> int:
        return self.parse_add()

    def parse_add(self) -> int:
        left: int = self.parse_mul()
        while True:
            if self.match("PLUS"):
                right: int = self.parse_mul()
                left = self.add_expr(ExprNode("bin", 0, "", "+", left, right))
                continue
            if self.match("MINUS"):
                right = self.parse_mul()
                left = self.add_expr(ExprNode("bin", 0, "", "-", left, right))
                continue
            break
        return left

    def parse_mul(self) -> int:
        left: int = self.parse_unary()
        while True:
            if self.match("STAR"):
                right: int = self.parse_unary()
                left = self.add_expr(ExprNode("bin", 0, "", "*", left, right))
                continue
            if self.match("SLASH"):
                right = self.parse_unary()
                left = self.add_expr(ExprNode("bin", 0, "", "/", left, right))
                continue
            break
        return left

    def parse_unary(self) -> int:
        if self.match("MINUS"):
            child: int = self.parse_unary()
            return self.add_expr(ExprNode("neg", 0, "", "", child, -1))
        return self.parse_primary()

    def parse_primary(self) -> int:
        if self.match("NUMBER"):
            token_num: Token = self.tokens[self.pos - 1]
            return self.add_expr(ExprNode("lit", int(token_num.text), "", "", -1, -1))

        if self.match("IDENT"):
            token_ident: Token = self.tokens[self.pos - 1]
            return self.add_expr(ExprNode("var", 0, token_ident.text, "", -1, -1))

        if self.match("LPAREN"):
            expr_index: int = self.parse_expr()
            self.expect("RPAREN")
            return expr_index

        t = self.tokens[self.pos]
        raise RuntimeError("primary parse error at pos=" + str(t.pos) + " got=" + t.kind)


def eval_expr(expr_index: int, expr_nodes: list[ExprNode], env: dict[str, int]) -> int:
    node: ExprNode = expr_nodes[expr_index]

    if node.kind == "lit":
        return node.value

    if node.kind == "var":
        if not (node.name in env):
            raise RuntimeError("undefined variable: " + node.name)
        return env[node.name]

    if node.kind == "neg":
        return -eval_expr(node.left, expr_nodes, env)

    if node.kind == "bin":
        lhs: int = eval_expr(node.left, expr_nodes, env)
        rhs: int = eval_expr(node.right, expr_nodes, env)
        if node.op == "+":
            return lhs + rhs
        if node.op == "-":
            return lhs - rhs
        if node.op == "*":
            return lhs * rhs
        if node.op == "/":
            if rhs == 0:
                raise RuntimeError("division by zero")
            # The mini-language uses integer division.
            return lhs // rhs
        raise RuntimeError("unknown operator: " + node.op)

    raise RuntimeError("unknown node kind: " + node.kind)


def execute(stmts: list[StmtNode], expr_nodes: list[ExprNode], trace: bool) -> int:
    env: dict[str, int] = {}
    checksum: int = 0
    printed: int = 0

    for stmt in stmts:
        if stmt.kind == "let":
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            continue

        if stmt.kind == "assign":
            if not (stmt.name in env):
                raise RuntimeError("assign to undefined variable: " + stmt.name)
            env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
            continue

        value: int = eval_expr(stmt.expr_index, expr_nodes, env)
        if trace:
            print(value)
        norm: int = value % 1000000007
        if norm < 0:
            norm += 1000000007
        checksum = (checksum * 131 + norm) % 1000000007
        printed += 1

    if trace:
        print("printed:", printed)
    return checksum


def build_benchmark_source(var_count: int, loops: int) -> list[str]:
    lines: list[str] = []

    # Declare initial variables.
    for i in range(var_count):
        lines.append("let v" + str(i) + " = " + str(i + 1))

    # Force evaluation of many arithmetic expressions.
    for i in range(loops):
        x: int = i % var_count
        y: int = (i + 3) % var_count
        c1: int = (i % 7) + 1
        c2: int = (i % 11) + 2
        lines.append(
            "v" + str(x) + " = (v" + str(x) + " * " + str(c1) + " + v" + str(y) + " + 10000) / " + str(c2)
        )
        if i % 97 == 0:
            lines.append("print v" + str(x))

    # Print final values together.
    lines.append("print (v0 + v1 + v2 + v3)")
    return lines


def run_demo() -> None:
    demo_lines: list[str] = []
    demo_lines.append("let a = 10")
    demo_lines.append("let b = 3")
    demo_lines.append("a = (a + b) * 2")
    demo_lines.append("print a")
    demo_lines.append("print a / b")

    tokens: list[Token] = tokenize(demo_lines)
    parser: Parser = Parser(tokens)
    stmts: list[StmtNode] = parser.parse_program()
    checksum: int = execute(stmts, parser.expr_nodes, True)
    print("demo_checksum:", checksum)


def run_benchmark() -> None:
    source_lines: list[str] = build_benchmark_source(32, 120000)
    start: float = perf_counter()
    tokens: list[Token] = tokenize(source_lines)
    parser: Parser = Parser(tokens)
    stmts: list[StmtNode] = parser.parse_program()
    checksum: int = execute(stmts, parser.expr_nodes, False)
    elapsed: float = perf_counter() - start

    print("token_count:", len(tokens))
    print("expr_count:", len(parser.expr_nodes))
    print("stmt_count:", len(stmts))
    print("checksum:", checksum)
    print("elapsed_sec:", elapsed)


def main() -> None:
    run_demo()
    run_benchmark()


if __name__ == "__main__":
    main()
