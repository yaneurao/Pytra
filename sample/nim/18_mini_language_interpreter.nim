include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

type Token* = ref object
  kind*: string
  text*: string
  pos*: int
  number_value*: int

type ExprNode* = ref object
  kind*: string
  value*: int
  name*: string
  op*: string
  left*: int
  right*: int
  kind_tag*: int
  op_tag*: int

type StmtNode* = ref object
  kind*: string
  name*: string
  expr_index*: int
  kind_tag*: int

proc tokenize*(lines: seq[string]): auto =
  var single_char_token_tags: Table[string, int] = { "+": 1, "-": 2, "*": 3, "/": 4, "(": 5, ")": 6, "=": 7 }.toTable
  var single_char_token_kinds: seq[string] = @["PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"]
  var tokens: seq[Token] = @[]
  for it in enumerate(lines):
    var i: int = 0
    var n: int = source.len
    while (i < n):
      var ch: string = source[i]
      if (ch == " "):
        i += 1
        discard `continue`
      var single_tag: int = /* unknown expr Unbox */
      if (single_tag > 0):
        tokens.add(newToken(single_char_token_kinds[(single_tag - 1)], ch, i, 0))
        i += 1
        discard `continue`
      if py_truthy(ch.isdigit()):
        var start: int = i
        while py_truthy(((i < n) {op} py_truthy(source[i].isdigit()))):
          i += 1
        var text: string = source[start ..< i]
        tokens.add(newToken("NUMBER", text, start, int(text)))
        discard `continue`
      if py_truthy((py_truthy(ch.isalpha()) {op} (ch == "_"))):
        start = i
        while py_truthy(((i < n) {op} py_truthy((py_truthy((py_truthy(source[i].isalpha()) {op} (source[i] == "_"))) {op} py_truthy(source[i].isdigit()))))):
          i += 1
        text = source[start ..< i]
        if (text == "let"):
          tokens.add(newToken("LET", text, start, 0))
        elif (text == "print"):
          tokens.add(newToken("PRINT", text, start, 0))
        else:
          tokens.add(newToken("IDENT", text, start, 0))
        discard `continue`
      raise newException(Exception, RuntimeError(((((("tokenize error at line=" & $( line_index )) & " pos=") & $( i )) & " ch=") & ch)))
    tokens.add(newToken("NEWLINE", "", n, 0))
  tokens.add(newToken("EOF", "", lines.len, 0))
  return tokens

type Parser* = ref object
  discard

proc new_expr_nodes*(self: Parser): auto =
  return @[]

proc newParser*(tokens: seq[Token]): Parser =
  new(result)
  result.tokens = tokens # seq[Token]
  result.pos = 0 # int
  result.expr_nodes = result.new_expr_nodes() # seq[ExprNode]

proc current_token*(self: Parser): auto =
  return self.tokens[self.pos]

proc previous_token*(self: Parser): auto =
  return self.tokens[(self.pos - 1)]

proc peek_kind*(self: Parser): auto =
  return self.current_token().kind

proc match*(self: Parser, kind: string): auto =
  if (self.peek_kind() == kind):
    self.pos += 1
    return true
  return false

proc expect*(self: Parser, kind: string): auto =
  var token: Token = self.current_token()
  if (token.kind != kind):
    raise newException(Exception, RuntimeError(((((("parse error at pos=" & /* unknown expr ObjStr */) & ", expected=") & kind) & ", got=") + token.kind)))
  self.pos += 1
  return token

proc skip_newlines*(self: Parser): auto =
  while py_truthy(self.match("NEWLINE")):
    discard

proc add_expr*(self: Parser, node: ExprNode): auto =
  self.expr_nodes.add(node)
  return (self.expr_nodes.len - 1)

proc parse_program*(self: Parser): auto =
  var stmts: seq[StmtNode] = @[]
  discard self.skip_newlines()
  while (self.peek_kind() != "EOF"):
    var stmt: StmtNode = self.parse_stmt()
    stmts.add(stmt)
    discard self.skip_newlines()
  return stmts

proc parse_stmt*(self: Parser): auto =
  if py_truthy(self.match("LET")):
    var let_name: string = /* unknown expr Unbox */
    discard self.expect("EQUAL")
    var let_expr_index: int = self.parse_expr()
    return newStmtNode("let", let_name, let_expr_index, 1)
  if py_truthy(self.match("PRINT")):
    var print_expr_index: int = self.parse_expr()
    return newStmtNode("print", "", print_expr_index, 3)
  var assign_name: string = /* unknown expr Unbox */
  discard self.expect("EQUAL")
  var assign_expr_index: int = self.parse_expr()
  return newStmtNode("assign", assign_name, assign_expr_index, 2)

proc parse_expr*(self: Parser): auto =
  return self.parse_add()

proc parse_add*(self: Parser): auto =
  var left: int = self.parse_mul()
  while true:
    if py_truthy(self.match("PLUS")):
      var right: int = self.parse_mul()
      left = self.add_expr(newExprNode("bin", 0, "", "+", left, right, 3, 1))
      discard `continue`
    if py_truthy(self.match("MINUS")):
      right = self.parse_mul()
      left = self.add_expr(newExprNode("bin", 0, "", "-", left, right, 3, 2))
      discard `continue`
    discard `break`
  return left

proc parse_mul*(self: Parser): auto =
  var left: int = self.parse_unary()
  while true:
    if py_truthy(self.match("STAR")):
      var right: int = self.parse_unary()
      left = self.add_expr(newExprNode("bin", 0, "", "*", left, right, 3, 3))
      discard `continue`
    if py_truthy(self.match("SLASH")):
      right = self.parse_unary()
      left = self.add_expr(newExprNode("bin", 0, "", "/", left, right, 3, 4))
      discard `continue`
    discard `break`
  return left

proc parse_unary*(self: Parser): auto =
  if py_truthy(self.match("MINUS")):
    var child: int = self.parse_unary()
    return self.add_expr(newExprNode("neg", 0, "", "", child, (-1), 4, 0))
  return self.parse_primary()

proc parse_primary*(self: Parser): auto =
  if py_truthy(self.match("NUMBER")):
    var token_num: Token = self.previous_token()
    return self.add_expr(newExprNode("lit", token_num.number_value, "", "", (-1), (-1), 1, 0))
  if py_truthy(self.match("IDENT")):
    var token_ident: Token = self.previous_token()
    return self.add_expr(newExprNode("var", 0, token_ident.text, "", (-1), (-1), 2, 0))
  if py_truthy(self.match("LPAREN")):
    var expr_index: int = self.parse_expr()
    discard self.expect("RPAREN")
    return expr_index
  var t = self.current_token()
  raise newException(Exception, RuntimeError(((("primary parse error at pos=" & /* unknown expr ObjStr */) & " got=") + t.kind)))

proc eval_expr*(expr_index: int, expr_nodes: seq[ExprNode], env: Table[string, int]): auto =
  var node: ExprNode = expr_nodes[expr_index]
  if (node.kind_tag == 1):
    return node.value
  if (node.kind_tag == 2):
    if py_truthy((not (node.name == env))):
      raise newException(Exception, RuntimeError(("undefined variable: " + node.name)))
    return env[node.name]
  if (node.kind_tag == 4):
    return (-eval_expr(node.left, expr_nodes, env))
  if (node.kind_tag == 3):
    var lhs: int = eval_expr(node.left, expr_nodes, env)
    var rhs: int = eval_expr(node.right, expr_nodes, env)
    if (node.op_tag == 1):
      return (lhs + rhs)
    if (node.op_tag == 2):
      return (lhs - rhs)
    if (node.op_tag == 3):
      return (lhs * rhs)
    if (node.op_tag == 4):
      if (rhs == 0):
        raise newException(Exception, RuntimeError("division by zero"))
      return (lhs div rhs)
    raise newException(Exception, RuntimeError(("unknown operator: " + node.op)))
  raise newException(Exception, RuntimeError(("unknown node kind: " + node.kind)))

proc execute*(stmts: seq[StmtNode], expr_nodes: seq[ExprNode], trace: bool): auto =
  var env: Table[string, int] = {  }.toTable
  var checksum: int = 0
  var printed: int = 0
  for stmt in stmts:
    if (stmt.kind_tag == 1):
      env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
      discard `continue`
    if (stmt.kind_tag == 2):
      if py_truthy((not (stmt.name == env))):
        raise newException(Exception, RuntimeError(("assign to undefined variable: " + stmt.name)))
      env[stmt.name] = eval_expr(stmt.expr_index, expr_nodes, env)
      discard `continue`
    var value: int = eval_expr(stmt.expr_index, expr_nodes, env)
    if py_truthy(trace):
      echo value
    var norm: int = py_mod(value, 1000000007)
    if (norm < 0):
      norm += 1000000007
    checksum = py_mod(((checksum * 131) + norm), 1000000007)
    printed += 1
  if py_truthy(trace):
    echo "printed:", printed
  return checksum

proc build_benchmark_source*(var_count: int, loops: int): auto =
  var lines: seq[string] = @[]
  for i in 0 ..< var_count:
    lines.add(((("let v" & $( i )) & " = ") & $( (i + 1) )))
  for i in 0 ..< loops:
    var x: int = py_mod(i, var_count)
    var y: int = py_mod((i + 3), var_count)
    var c1: int = (py_mod(i, 7) + 1)
    var c2: int = (py_mod(i, 11) + 2)
    lines.add(((((((((("v" & $( x )) & " = (v") & $( x )) & " * ") & $( c1 )) & " + v") & $( y )) & " + 10000) / ") & $( c2 )))
    if (py_mod(i, 97) == 0):
      lines.add(("print v" & $( x )))
  lines.add("print (v0 + v1 + v2 + v3)")
  return lines

proc run_demo*(): auto =
  var demo_lines: seq[string] = @[]
  demo_lines.add("let a = 10")
  demo_lines.add("let b = 3")
  demo_lines.add("a = (a + b) * 2")
  demo_lines.add("print a")
  demo_lines.add("print a / b")
  var tokens: seq[Token] = tokenize(demo_lines)
  var parser: Parser = newParser(tokens)
  var stmts: seq[StmtNode] = parser.parse_program()
  var checksum: int = execute(stmts, parser.expr_nodes, true)
  echo "demo_checksum:", checksum

proc run_benchmark*(): auto =
  var source_lines: seq[string] = build_benchmark_source(32, 120000)
  var start: float = epochTime()
  var tokens: seq[Token] = tokenize(source_lines)
  var parser: Parser = newParser(tokens)
  var stmts: seq[StmtNode] = parser.parse_program()
  var checksum: int = execute(stmts, parser.expr_nodes, false)
  var elapsed: float = (epochTime() - start)
  echo "token_count:", tokens.len
  echo "expr_count:", /* unknown expr ObjLen */
  echo "stmt_count:", stmts.len
  echo "checksum:", checksum
  echo "elapsed_sec:", elapsed

proc v_pytra_main*(): auto =
  run_demo()
  run_benchmark()


if isMainModule:
  discard main()
