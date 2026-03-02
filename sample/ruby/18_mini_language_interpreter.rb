require_relative "py_runtime"


class Token
  attr_accessor :kind, :text, :pos, :number_value

  def initialize(kind, text, pos, number_value)
    self.kind = kind
    self.text = text
    self.pos = pos
    self.number_value = number_value
  end
end

class ExprNode
  attr_accessor :kind, :value, :name, :op, :left, :right, :kind_tag, :op_tag

  def initialize(kind, value, name, op, left, right, kind_tag, op_tag)
    self.kind = kind
    self.value = value
    self.name = name
    self.op = op
    self.left = left
    self.right = right
    self.kind_tag = kind_tag
    self.op_tag = op_tag
  end
end

class StmtNode
  attr_accessor :kind, :name, :expr_index, :kind_tag

  def initialize(kind, name, expr_index, kind_tag)
    self.kind = kind
    self.name = name
    self.expr_index = expr_index
    self.kind_tag = kind_tag
  end
end

class Parser
  attr_accessor :tokens, :pos, :expr_nodes

  def new_expr_nodes()
    return []
  end

  def initialize(tokens)
    self.tokens = tokens
    self.pos = 0
    self.expr_nodes = self.new_expr_nodes()
  end

  def current_token()
    return __pytra_get_index(self.tokens, self.pos)
  end

  def previous_token()
    return __pytra_get_index(self.tokens, self.pos - 1)
  end

  def peek_kind()
    return self.current_token().kind
  end

  def match(kind)
    if self.peek_kind() == kind
      self.pos += 1
      return true
    end
    return false
  end

  def expect(kind)
    token = self.current_token()
    if token.kind != kind
      raise RuntimeError, __pytra_str(((((("parse error at pos=" + __pytra_str(token.pos)) + ", expected=") + kind) + ", got=") + token.kind))
    end
    self.pos += 1
    return token
  end

  def skip_newlines()
    while self.match("NEWLINE")
      nil
    end
  end

  def add_expr(node)
    self.expr_nodes.append(node)
    return __pytra_len(self.expr_nodes) - 1
  end

  def parse_program()
    stmts = []
    self.skip_newlines()
    while self.peek_kind() != "EOF"
      stmt = self.parse_stmt()
      stmts.append(stmt)
      self.skip_newlines()
    end
    return stmts
  end

  def parse_stmt()
    if self.match("LET")
      let_name = self.expect("IDENT").text
      self.expect("EQUAL")
      let_expr_index = self.parse_expr()
      return StmtNode.new("let", let_name, let_expr_index, 1)
    end
    if self.match("PRINT")
      print_expr_index = self.parse_expr()
      return StmtNode.new("print", "", print_expr_index, 3)
    end
    assign_name = self.expect("IDENT").text
    self.expect("EQUAL")
    assign_expr_index = self.parse_expr()
    return StmtNode.new("assign", assign_name, assign_expr_index, 2)
  end

  def parse_expr()
    return self.parse_add()
  end

  def parse_add()
    left = self.parse_mul()
    while true
      if self.match("PLUS")
        right = self.parse_mul()
        left = self.add_expr(ExprNode.new("bin", 0, "", "+", left, right, 3, 1))
        next
      end
      if self.match("MINUS")
        right = self.parse_mul()
        left = self.add_expr(ExprNode.new("bin", 0, "", "-", left, right, 3, 2))
        next
      end
      break
    end
    return left
  end

  def parse_mul()
    left = self.parse_unary()
    while true
      if self.match("STAR")
        right = self.parse_unary()
        left = self.add_expr(ExprNode.new("bin", 0, "", "*", left, right, 3, 3))
        next
      end
      if self.match("SLASH")
        right = self.parse_unary()
        left = self.add_expr(ExprNode.new("bin", 0, "", "/", left, right, 3, 4))
        next
      end
      break
    end
    return left
  end

  def parse_unary()
    if self.match("MINUS")
      child = self.parse_unary()
      return self.add_expr(ExprNode.new("neg", 0, "", "", child, (-1), 4, 0))
    end
    return self.parse_primary()
  end

  def parse_primary()
    if self.match("NUMBER")
      token_num = self.previous_token()
      return self.add_expr(ExprNode.new("lit", token_num.number_value, "", "", (-1), (-1), 1, 0))
    end
    if self.match("IDENT")
      token_ident = self.previous_token()
      return self.add_expr(ExprNode.new("var", 0, token_ident.text, "", (-1), (-1), 2, 0))
    end
    if self.match("LPAREN")
      expr_index = self.parse_expr()
      self.expect("RPAREN")
      return expr_index
    end
    t = self.current_token()
    raise RuntimeError, __pytra_str(((("primary parse error at pos=" + __pytra_str(t.pos)) + " got=") + t.kind))
  end
end

def tokenize(lines)
  single_char_token_tags = {}
  single_char_token_kinds = ["PLUS", "MINUS", "STAR", "SLASH", "LPAREN", "RPAREN", "EQUAL"]
  tokens = []
  __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
  for __it_1 in __iter_0
    __tuple_2 = __pytra_as_list(__it_1)
    line_index = __tuple_2[0]
    source = __tuple_2[1]
    i = 0
    n = __pytra_len(source)
    while i < n
      ch = __pytra_get_index(source, i)
      if ch == " "
        i += 1
        next
      end
      single_tag = __pytra_as_dict(single_char_token_tags).fetch(ch, 0)
      if single_tag > 0
        tokens.append(Token.new(__pytra_get_index(single_char_token_kinds, single_tag - 1), ch, i, 0))
        i += 1
        next
      end
      if __pytra_truthy(__pytra_isdigit(ch))
        start = i
        while (i < n) && __pytra_truthy(__pytra_isdigit(__pytra_get_index(source, i)))
          i += 1
        end
        text = __pytra_slice(source, start, i)
        tokens.append(Token.new("NUMBER", text, start, __pytra_int(text)))
        next
      end
      if __pytra_truthy(__pytra_isalpha(ch)) || (ch == "_")
        start = i
        while (i < n) && ((__pytra_truthy(__pytra_isalpha(__pytra_get_index(source, i))) || (__pytra_get_index(source, i) == "_")) || __pytra_truthy(__pytra_isdigit(__pytra_get_index(source, i))))
          i += 1
        end
        text = __pytra_slice(source, start, i)
        if text == "let"
          tokens.append(Token.new("LET", text, start, 0))
        else
          if text == "print"
            tokens.append(Token.new("PRINT", text, start, 0))
          else
            tokens.append(Token.new("IDENT", text, start, 0))
          end
        end
        next
      end
      raise RuntimeError, __pytra_str((((("tokenize error at line=" + __pytra_str(line_index) + " pos=") + __pytra_str(i)) + " ch=") + ch))
    end
    tokens.append(Token.new("NEWLINE", "", n, 0))
  end
  tokens.append(Token.new("EOF", "", __pytra_len(lines), 0))
  return tokens
end

def eval_expr(expr_index, expr_nodes, env)
  node = __pytra_get_index(expr_nodes, expr_index)
  if node.kind_tag == 1
    return node.value
  end
  if node.kind_tag == 2
    if !__pytra_contains(env, node.name)
      raise RuntimeError, __pytra_str("undefined variable: " + node.name)
    end
    return __pytra_get_index(env, node.name)
  end
  if node.kind_tag == 4
    return (-eval_expr(node.left, expr_nodes, env))
  end
  if node.kind_tag == 3
    lhs = eval_expr(node.left, expr_nodes, env)
    rhs = eval_expr(node.right, expr_nodes, env)
    if node.op_tag == 1
      return lhs + rhs
    end
    if node.op_tag == 2
      return lhs - rhs
    end
    if node.op_tag == 3
      return lhs * rhs
    end
    if node.op_tag == 4
      if rhs == 0
        raise RuntimeError, __pytra_str("division by zero")
      end
      return lhs / rhs
    end
    raise RuntimeError, __pytra_str("unknown operator: " + node.op)
  end
  raise RuntimeError, __pytra_str("unknown node kind: " + node.kind)
end

def execute(stmts, expr_nodes, trace)
  env = {}
  checksum = 0
  printed = 0
  for stmt in __pytra_as_list(stmts)
    if stmt.kind_tag == 1
      __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
      next
    end
    if stmt.kind_tag == 2
      if !__pytra_contains(env, stmt.name)
        raise RuntimeError, __pytra_str("assign to undefined variable: " + stmt.name)
      end
      __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
      next
    end
    value = eval_expr(stmt.expr_index, expr_nodes, env)
    if trace
      __pytra_print(value)
    end
    norm = value % 1000000007
    if norm < 0
      norm += 1000000007
    end
    checksum = ((checksum * 131 + norm) % 1000000007)
    printed += 1
  end
  if trace
    __pytra_print("printed:", printed)
  end
  return checksum
end

def build_benchmark_source(var_count, loops)
  lines = []
  i = 0
  while i < var_count
    lines.append((("let v" + __pytra_str(i) + " = ") + __pytra_str(i + 1)))
    i += 1
  end
  i = 0
  while i < loops
    x = i % var_count
    y = ((i + 3) % var_count)
    c1 = (i % 7 + 1)
    c2 = (i % 11 + 2)
    lines.append((((((((("v" + __pytra_str(x) + " = (v") + __pytra_str(x)) + " * ") + __pytra_str(c1)) + " + v") + __pytra_str(y)) + " + 10000) / ") + __pytra_str(c2)))
    if i % 97 == 0
      lines.append("print v" + __pytra_str(x))
    end
    i += 1
  end
  lines.append("print (v0 + v1 + v2 + v3)")
  return lines
end

def run_demo()
  demo_lines = []
  demo_lines.concat(["let a = 10", "let b = 3", "a = (a + b) * 2", "print a", "print a / b"])
  tokens = tokenize(demo_lines)
  parser = Parser.new(tokens)
  stmts = parser.parse_program()
  checksum = execute(stmts, parser.expr_nodes, true)
  __pytra_print("demo_checksum:", checksum)
end

def run_benchmark()
  source_lines = build_benchmark_source(32, 120000)
  start = __pytra_perf_counter()
  tokens = tokenize(source_lines)
  parser = Parser.new(tokens)
  stmts = parser.parse_program()
  checksum = execute(stmts, parser.expr_nodes, false)
  elapsed = __pytra_perf_counter() - start
  __pytra_print("token_count:", __pytra_len(tokens))
  __pytra_print("expr_count:", __pytra_len(parser.expr_nodes))
  __pytra_print("stmt_count:", __pytra_len(stmts))
  __pytra_print("checksum:", checksum)
  __pytra_print("elapsed_sec:", elapsed)
end

def __pytra_main()
  run_demo()
  run_benchmark()
end

if __FILE__ == $PROGRAM_NAME
  __pytra_main()
end
