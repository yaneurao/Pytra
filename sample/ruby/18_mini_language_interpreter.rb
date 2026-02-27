# Auto-generated Pytra Ruby native source from EAST3.

def __pytra_noop(*args)
  nil
end

def __pytra_assert(*args)
  "True"
end

def __pytra_perf_counter
  Process.clock_gettime(Process::CLOCK_MONOTONIC)
end

def __pytra_truthy(v)
  return false if v.nil?
  return v if v == true || v == false
  return v != 0 if v.is_a?(Integer)
  return v != 0.0 if v.is_a?(Float)
  return !v.empty? if v.respond_to?(:empty?)
  true
end

def __pytra_int(v)
  return 0 if v.nil?
  return v.to_i
end

def __pytra_float(v)
  return 0.0 if v.nil?
  return v.to_f
end

def __pytra_str(v)
  return "" if v.nil?
  v.to_s
end

def __pytra_len(v)
  return 0 if v.nil?
  return v.length if v.respond_to?(:length)
  0
end

def __pytra_as_list(v)
  return v if v.is_a?(Array)
  return v.to_a if v.respond_to?(:to_a)
  []
end

def __pytra_as_dict(v)
  return v if v.is_a?(Hash)
  {}
end

def __pytra_bytearray(v=nil)
  return [] if v.nil?
  if v.is_a?(Integer)
    n = v
    n = 0 if n < 0
    return Array.new(n, 0)
  end
  if v.is_a?(String)
    return v.bytes
  end
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_bytes(v)
  return [] if v.nil?
  return v.bytes if v.is_a?(String)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << i
    i += step
  end
  out
end

def __pytra_list_comp_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << yield(i)
    i += step
  end
  out
end

def __pytra_enumerate(v)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << [i, src[i]]
    i += 1
  end
  out
end

def __pytra_abs(v)
  x = __pytra_float(v)
  x < 0 ? -x : x
end

def __pytra_get_index(container, index)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return nil if i < 0 || i >= container.length
    return container[i]
  end
  if container.is_a?(Hash)
    return container[index]
  end
  if container.is_a?(String)
    i = __pytra_int(index)
    i += container.length if i < 0
    return "" if i < 0 || i >= container.length
    return container[i] || ""
  end
  nil
end

def __pytra_set_index(container, index, value)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return if i < 0 || i >= container.length
    container[i] = value
    return
  end
  if container.is_a?(Hash)
    container[index] = value
  end
end

def __pytra_slice(container, lower, upper)
  return nil if container.nil?
  lo = __pytra_int(lower)
  hi = __pytra_int(upper)
  return container[lo...hi]
end

def __pytra_min(a, b)
  __pytra_float(a) < __pytra_float(b) ? a : b
end

def __pytra_max(a, b)
  __pytra_float(a) > __pytra_float(b) ? a : b
end

def __pytra_isdigit(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[0-9]+\z/)
end

def __pytra_isalpha(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[A-Za-z]+\z/)
end

def __pytra_print(*args)
  if args.empty?
    puts
    return
  end
  puts(args.map { |x| __pytra_str(x) }.join(" "))
end

class Token
  attr_accessor :kind, :text, :pos

  def initialize(kind, text, pos)
    self.kind = kind
    self.text = text
    self.pos = pos
  end
end

class ExprNode
  attr_accessor :kind, :value, :name, :op, :left, :right

  def initialize(kind, value, name, op, left, right)
    self.kind = kind
    self.value = value
    self.name = name
    self.op = op
    self.left = left
    self.right = right
  end
end

class StmtNode
  attr_accessor :kind, :name, :expr_index

  def initialize(kind, name, expr_index)
    self.kind = kind
    self.name = name
    self.expr_index = expr_index
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

  def peek_kind()
    return __pytra_get_index(self.tokens, self.pos).kind
  end

  def match(kind)
    if __pytra_truthy((self.peek_kind() == kind))
      self.pos += 1
      return true
    end
    return false
  end

  def expect(kind)
    if __pytra_truthy((self.peek_kind() != kind))
      t = __pytra_get_index(self.tokens, self.pos)
      raise RuntimeError, __pytra_str(((((("parse error at pos=" + __pytra_str(t.pos)) + ", expected=") + kind) + ", got=") + t.kind))
    end
    token = __pytra_get_index(self.tokens, self.pos)
    self.pos += 1
    return token
  end

  def skip_newlines()
    while __pytra_truthy(self.match("NEWLINE"))
      # pass
    end
  end

  def add_expr(node)
    self.expr_nodes.append(node)
    return (__pytra_len(self.expr_nodes) - 1)
  end

  def parse_program()
    stmts = []
    self.skip_newlines()
    while __pytra_truthy((self.peek_kind() != "EOF"))
      stmt = self.parse_stmt()
      stmts.append(stmt)
      self.skip_newlines()
    end
    return stmts
  end

  def parse_stmt()
    if __pytra_truthy(self.match("LET"))
      let_name = self.expect("IDENT").text
      self.expect("EQUAL")
      let_expr_index = self.parse_expr()
      return StmtNode.new("let", let_name, let_expr_index)
    end
    if __pytra_truthy(self.match("PRINT"))
      print_expr_index = self.parse_expr()
      return StmtNode.new("print", "", print_expr_index)
    end
    assign_name = self.expect("IDENT").text
    self.expect("EQUAL")
    assign_expr_index = self.parse_expr()
    return StmtNode.new("assign", assign_name, assign_expr_index)
  end

  def parse_expr()
    return self.parse_add()
  end

  def parse_add()
    left = self.parse_mul()
    while __pytra_truthy(true)
      if __pytra_truthy(self.match("PLUS"))
        right = self.parse_mul()
        left = self.add_expr(ExprNode.new("bin", 0, "", "+", left, right))
        next
      end
      if __pytra_truthy(self.match("MINUS"))
        right = self.parse_mul()
        left = self.add_expr(ExprNode.new("bin", 0, "", "-", left, right))
        next
      end
      break
    end
    return left
  end

  def parse_mul()
    left = self.parse_unary()
    while __pytra_truthy(true)
      if __pytra_truthy(self.match("STAR"))
        right = self.parse_unary()
        left = self.add_expr(ExprNode.new("bin", 0, "", "*", left, right))
        next
      end
      if __pytra_truthy(self.match("SLASH"))
        right = self.parse_unary()
        left = self.add_expr(ExprNode.new("bin", 0, "", "/", left, right))
        next
      end
      break
    end
    return left
  end

  def parse_unary()
    if __pytra_truthy(self.match("MINUS"))
      child = self.parse_unary()
      return self.add_expr(ExprNode.new("neg", 0, "", "", child, (-1)))
    end
    return self.parse_primary()
  end

  def parse_primary()
    if __pytra_truthy(self.match("NUMBER"))
      token_num = __pytra_get_index(self.tokens, (self.pos - 1))
      return self.add_expr(ExprNode.new("lit", __pytra_int(token_num.text), "", "", (-1), (-1)))
    end
    if __pytra_truthy(self.match("IDENT"))
      token_ident = __pytra_get_index(self.tokens, (self.pos - 1))
      return self.add_expr(ExprNode.new("var", 0, token_ident.text, "", (-1), (-1)))
    end
    if __pytra_truthy(self.match("LPAREN"))
      expr_index = self.parse_expr()
      self.expect("RPAREN")
      return expr_index
    end
    t = __pytra_get_index(self.tokens, self.pos)
    raise RuntimeError, __pytra_str(((("primary parse error at pos=" + __pytra_str(t.pos)) + " got=") + t.kind))
  end
end

def tokenize(lines)
  tokens = []
  __iter_0 = __pytra_as_list(__pytra_enumerate(lines))
  for __it_1 in __iter_0
    __tuple_2 = __pytra_as_list(__it_1)
    line_index = __tuple_2[0]
    source = __tuple_2[1]
    i = 0
    n = __pytra_len(source)
    while __pytra_truthy((i < n))
      ch = __pytra_get_index(source, i)
      if __pytra_truthy((ch == " "))
        i += 1
        next
      end
      if __pytra_truthy((ch == "+"))
        tokens.append(Token.new("PLUS", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == "-"))
        tokens.append(Token.new("MINUS", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == "*"))
        tokens.append(Token.new("STAR", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == "/"))
        tokens.append(Token.new("SLASH", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == "("))
        tokens.append(Token.new("LPAREN", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == ")"))
        tokens.append(Token.new("RPAREN", ch, i))
        i += 1
        next
      end
      if __pytra_truthy((ch == "="))
        tokens.append(Token.new("EQUAL", ch, i))
        i += 1
        next
      end
      if __pytra_truthy(__pytra_isdigit(ch))
        start = i
        while __pytra_truthy((__pytra_truthy((i < n)) && __pytra_truthy(__pytra_isdigit(__pytra_get_index(source, i)))))
          i += 1
        end
        text = __pytra_slice(source, start, i)
        tokens.append(Token.new("NUMBER", text, start))
        next
      end
      if __pytra_truthy((__pytra_truthy(__pytra_isalpha(ch)) || __pytra_truthy((ch == "_"))))
        start = i
        while __pytra_truthy((__pytra_truthy((i < n)) && __pytra_truthy((__pytra_truthy((__pytra_truthy(__pytra_isalpha(__pytra_get_index(source, i))) || __pytra_truthy((__pytra_get_index(source, i) == "_")))) || __pytra_truthy(__pytra_isdigit(__pytra_get_index(source, i)))))))
          i += 1
        end
        text = __pytra_slice(source, start, i)
        if __pytra_truthy((text == "let"))
          tokens.append(Token.new("LET", text, start))
        else
          if __pytra_truthy((text == "print"))
            tokens.append(Token.new("PRINT", text, start))
          else
            tokens.append(Token.new("IDENT", text, start))
          end
        end
        next
      end
      raise RuntimeError, __pytra_str(((((("tokenize error at line=" + __pytra_str(line_index)) + " pos=") + __pytra_str(i)) + " ch=") + ch))
    end
    tokens.append(Token.new("NEWLINE", "", n))
  end
  tokens.append(Token.new("EOF", "", __pytra_len(lines)))
  return tokens
end

def eval_expr(expr_index, expr_nodes, env)
  node = __pytra_get_index(expr_nodes, expr_index)
  if __pytra_truthy((node.kind == "lit"))
    return node.value
  end
  if __pytra_truthy((node.kind == "var"))
    if __pytra_truthy((!__pytra_truthy((node.name == env))))
      raise RuntimeError, __pytra_str(("undefined variable: " + node.name))
    end
    return __pytra_get_index(env, node.name)
  end
  if __pytra_truthy((node.kind == "neg"))
    return (-eval_expr(node.left, expr_nodes, env))
  end
  if __pytra_truthy((node.kind == "bin"))
    lhs = eval_expr(node.left, expr_nodes, env)
    rhs = eval_expr(node.right, expr_nodes, env)
    if __pytra_truthy((node.op == "+"))
      return (lhs + rhs)
    end
    if __pytra_truthy((node.op == "-"))
      return (lhs - rhs)
    end
    if __pytra_truthy((node.op == "*"))
      return (lhs * rhs)
    end
    if __pytra_truthy((node.op == "/"))
      if __pytra_truthy((rhs == 0))
        raise RuntimeError, __pytra_str("division by zero")
      end
      return (__pytra_int(lhs) / __pytra_int(rhs))
    end
    raise RuntimeError, __pytra_str(("unknown operator: " + node.op))
  end
  raise RuntimeError, __pytra_str(("unknown node kind: " + node.kind))
end

def execute(stmts, expr_nodes, trace)
  env = {}
  checksum = 0
  printed = 0
  for stmt in __pytra_as_list(stmts)
    if __pytra_truthy((stmt.kind == "let"))
      __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
      next
    end
    if __pytra_truthy((stmt.kind == "assign"))
      if __pytra_truthy((!__pytra_truthy((stmt.name == env))))
        raise RuntimeError, __pytra_str(("assign to undefined variable: " + stmt.name))
      end
      __pytra_set_index(env, stmt.name, eval_expr(stmt.expr_index, expr_nodes, env))
      next
    end
    value = eval_expr(stmt.expr_index, expr_nodes, env)
    if __pytra_truthy(trace)
      __pytra_print(value)
    end
    norm = (value % 1000000007)
    if __pytra_truthy((norm < 0))
      norm += 1000000007
    end
    checksum = (((checksum * 131) + norm) % 1000000007)
    printed += 1
  end
  if __pytra_truthy(trace)
    __pytra_print("printed:", printed)
  end
  return checksum
end

def build_benchmark_source(var_count, loops)
  lines = []
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(var_count)) || (__step_0 < 0 && i > __pytra_int(var_count)))
    lines.append(((("let v" + __pytra_str(i)) + " = ") + __pytra_str((i + 1))))
    i += __step_0
  end
  __step_1 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_1 >= 0 && i < __pytra_int(loops)) || (__step_1 < 0 && i > __pytra_int(loops)))
    x = (i % var_count)
    y = ((i + 3) % var_count)
    c1 = ((i % 7) + 1)
    c2 = ((i % 11) + 2)
    lines.append(((((((((("v" + __pytra_str(x)) + " = (v") + __pytra_str(x)) + " * ") + __pytra_str(c1)) + " + v") + __pytra_str(y)) + " + 10000) / ") + __pytra_str(c2)))
    if __pytra_truthy(((i % 97) == 0))
      lines.append(("print v" + __pytra_str(x)))
    end
    i += __step_1
  end
  lines.append("print (v0 + v1 + v2 + v3)")
  return lines
end

def run_demo()
  demo_lines = []
  demo_lines.append("let a = 10")
  demo_lines.append("let b = 3")
  demo_lines.append("a = (a + b) * 2")
  demo_lines.append("print a")
  demo_lines.append("print a / b")
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
  elapsed = (__pytra_perf_counter() - start)
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
  main()
end
