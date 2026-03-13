# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/re.py
# generated-by: tools/gen_runtime_from_manifest.py

require_relative "py_runtime"


class Match
  attr_accessor :_text, :_groups

  def initialize(text, groups)
    self._text = text
    self._groups = groups
  end

  def group(idx)
    if idx == 0
      return self._text
    end
    if (idx < 0) || (idx > __pytra_len(self._groups))
      raise RuntimeError, __pytra_str(IndexError("group index out of range"))
    end
    return __pytra_get_index(self._groups, idx - 1)
  end
end

def group(m, idx)
  if m == nil
    return ""
  end
  mm = m
  return mm.group(idx)
end

def strip_group(m, idx)
  return group(m, idx).strip()
end

def _is_ident(s)
  if s == ""
    return false
  end
  h = __pytra_slice(s, 0, 1)
  is_head_alpha = (("a" <= h) || ("A" <= h))
  if !(is_head_alpha || (h == "_"))
    return false
  end
  for ch in __pytra_as_list(__pytra_slice(s, 1, __pytra_len(s)))
    is_alpha = (("a" <= ch) || ("A" <= ch))
    is_digit = ("0" <= ch)
    if !(is_alpha || is_digit || (ch == "_"))
      return false
    end
  end
  return true
end

def _is_dotted_ident(s)
  if s == ""
    return false
  end
  part = ""
  for ch in __pytra_as_list(s)
    if ch == "."
      if !_is_ident(part)
        return false
      end
      part = ""
      next
    end
    part += ch
  end
  if !_is_ident(part)
    return false
  end
  if part == ""
    return false
  end
  return true
end

def _strip_suffix_colon(s)
  t = s.rstrip()
  if __pytra_len(t) == 0
    return ""
  end
  if __pytra_slice(t, (-1), __pytra_len(t)) != ":"
    return ""
  end
  return __pytra_slice(t, 0, (-1))
end

def _is_space_ch(ch)
  if ch == " "
    return true
  end
  if ch == "	"
    return true
  end
  if ch == ""
    return true
  end
  if ch == "\n"
    return true
  end
  return false
end

def _is_alnum_or_underscore(ch)
  is_alpha = (("a" <= ch) || ("A" <= ch))
  is_digit = ("0" <= ch)
  if is_alpha || is_digit
    return true
  end
  return (ch == "_")
end

def _skip_spaces(t, i)
  while i < __pytra_len(t)
    if !_is_space_ch(__pytra_slice(t, i, i + 1))
      return i
    end
    i += 1
  end
  return i
end

def match(pattern, text, flags)
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$"
    if !__pytra_truthy(text.endswith("]"))
      return nil
    end
    i = text.find("[")
    if i <= 0
      return nil
    end
    head = __pytra_slice(text, 0, i)
    if !_is_ident(head)
      return nil
    end
    return Match.new(text, [head, __pytra_slice(text, i + 1, (-1))])
  end
  if pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$"
    t = _strip_suffix_colon(text)
    if t == ""
      return nil
    end
    i = 0
    if !__pytra_truthy(t.startswith("def"))
      return nil
    end
    i = 3
    if (i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, i + 1)))
      return nil
    end
    i = _skip_spaces(t, i)
    j = i
    while (j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, j + 1))
      j += 1
    end
    name = __pytra_slice(t, i, j)
    if !_is_ident(name)
      return nil
    end
    k = j
    k = _skip_spaces(t, k)
    if (k >= __pytra_len(t)) || (__pytra_slice(t, k, k + 1) != "(")
      return nil
    end
    r = t.rfind(")")
    if r <= k
      return nil
    end
    args = __pytra_slice(t, k + 1, r)
    tail = __pytra_slice(t, r + 1, __pytra_len(t)).strip()
    if tail == ""
      return Match.new(text, [name, args, ""])
    end
    if !__pytra_truthy(tail.startswith("->"))
      return nil
    end
    ret = __pytra_slice(tail, 2, __pytra_len(tail)).strip()
    if ret == ""
      return nil
    end
    return Match.new(text, [name, args, ret])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$"
    c = text.find(":")
    if c <= 0
      return nil
    end
    name = __pytra_slice(text, 0, c).strip()
    if !_is_ident(name)
      return nil
    end
    rhs = __pytra_slice(text, c + 1, __pytra_len(text))
    eq = rhs.find("=")
    if eq < 0
      ann = rhs.strip()
      if ann == ""
        return nil
      end
      return Match.new(text, [name, ann, ""])
    end
    ann = __pytra_slice(rhs, 0, eq).strip()
    val = __pytra_slice(rhs, eq + 1, __pytra_len(rhs)).strip()
    if (ann == "") || (val == "")
      return nil
    end
    return Match.new(text, [name, ann, val])
  end
  if pattern == "^[A-Za-z_][A-Za-z0-9_]*$"
    if _is_ident(text)
      return Match.new(text, [])
    end
    return nil
  end
  if pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$"
    t = _strip_suffix_colon(text)
    if t == ""
      return nil
    end
    if !__pytra_truthy(t.startswith("class"))
      return nil
    end
    i = 5
    if (i >= __pytra_len(t)) || (!_is_space_ch(__pytra_slice(t, i, i + 1)))
      return nil
    end
    i = _skip_spaces(t, i)
    j = i
    while (j < __pytra_len(t)) && _is_alnum_or_underscore(__pytra_slice(t, j, j + 1))
      j += 1
    end
    name = __pytra_slice(t, i, j)
    if !_is_ident(name)
      return nil
    end
    tail = __pytra_slice(t, j, __pytra_len(t)).strip()
    if tail == ""
      return Match.new(text, [name, ""])
    end
    if !(__pytra_truthy(tail.startswith("(")) && __pytra_truthy(tail.endswith(")")))
      return nil
    end
    base = __pytra_slice(tail, 1, (-1)).strip()
    if !_is_ident(base)
      return nil
    end
    return Match.new(text, [name, base])
  end
  if pattern == "^(any|all)\\((.+)\\)$"
    if __pytra_truthy(text.startswith("any(")) && __pytra_truthy(text.endswith(")")) && (__pytra_len(text) > 5)
      return Match.new(text, ["any", __pytra_slice(text, 4, (-1))])
    end
    if __pytra_truthy(text.startswith("all(")) && __pytra_truthy(text.endswith(")")) && (__pytra_len(text) > 5)
      return Match.new(text, ["all", __pytra_slice(text, 4, (-1))])
    end
    return nil
  end
  if pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$"
    if !(__pytra_truthy(text.startswith("[")) && __pytra_truthy(text.endswith("]")))
      return nil
    end
    inner = __pytra_slice(text, 1, (-1)).strip()
    m1 = " for "
    m2 = " in "
    i = inner.find(m1)
    if i < 0
      return nil
    end
    expr = __pytra_slice(inner, 0, i).strip()
    rest = __pytra_slice(inner, i + __pytra_len(m1), __pytra_len(inner))
    j = rest.find(m2)
    if j < 0
      return nil
    end
    var = __pytra_slice(rest, 0, j).strip()
    it = __pytra_slice(rest, j + __pytra_len(m2), __pytra_len(rest)).strip()
    if (!_is_ident(expr)) || (!_is_ident(var)) || (it == "")
      return nil
    end
    return Match.new(text, [expr, var, it])
  end
  if pattern == "^for\\s+(.+)\\s+in\\s+(.+):$"
    t = _strip_suffix_colon(text)
    if (t == "") || (!__pytra_truthy(t.startswith("for")))
      return nil
    end
    rest = __pytra_slice(t, 3, __pytra_len(t)).strip()
    i = rest.find(" in ")
    if i < 0
      return nil
    end
    left = __pytra_slice(rest, 0, i).strip()
    right = __pytra_slice(rest, i + 4, __pytra_len(rest)).strip()
    if (left == "") || (right == "")
      return nil
    end
    return Match.new(text, [left, right])
  end
  if pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"
    t = _strip_suffix_colon(text)
    if (t == "") || (!__pytra_truthy(t.startswith("with")))
      return nil
    end
    rest = __pytra_slice(t, 4, __pytra_len(t)).strip()
    i = rest.rfind(" as ")
    if i < 0
      return nil
    end
    expr = __pytra_slice(rest, 0, i).strip()
    name = __pytra_slice(rest, i + 4, __pytra_len(rest)).strip()
    if (expr == "") || (!_is_ident(name))
      return nil
    end
    return Match.new(text, [expr, name])
  end
  if pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"
    t = _strip_suffix_colon(text)
    if (t == "") || (!__pytra_truthy(t.startswith("except")))
      return nil
    end
    rest = __pytra_slice(t, 6, __pytra_len(t)).strip()
    i = rest.rfind(" as ")
    if i < 0
      return nil
    end
    exc = __pytra_slice(rest, 0, i).strip()
    name = __pytra_slice(rest, i + 4, __pytra_len(rest)).strip()
    if (exc == "") || (!_is_ident(name))
      return nil
    end
    return Match.new(text, [exc, name])
  end
  if pattern == "^except\\s+(.+?)\\s*:\\s*$"
    t = _strip_suffix_colon(text)
    if (t == "") || (!__pytra_truthy(t.startswith("except")))
      return nil
    end
    rest = __pytra_slice(t, 6, __pytra_len(t)).strip()
    if rest == ""
      return nil
    end
    return Match.new(text, [rest])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$"
    c = text.find(":")
    if c <= 0
      return nil
    end
    target = __pytra_slice(text, 0, c).strip()
    ann = __pytra_slice(text, c + 1, __pytra_len(text)).strip()
    if (ann == "") || (!_is_dotted_ident(target))
      return nil
    end
    return Match.new(text, [target, ann])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"
    c = text.find(":")
    if c <= 0
      return nil
    end
    target = __pytra_slice(text, 0, c).strip()
    rhs = __pytra_slice(text, c + 1, __pytra_len(text))
    eq = rhs.find("=")
    if eq < 0
      return nil
    end
    ann = __pytra_slice(rhs, 0, eq).strip()
    expr = __pytra_slice(rhs, eq + 1, __pytra_len(rhs)).strip()
    if (!_is_dotted_ident(target)) || (ann == "") || (expr == "")
      return nil
    end
    return Match.new(text, [target, ann, expr])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$"
    ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="]
    op_pos = (-1)
    op_txt = ""
    for op in __pytra_as_list(ops)
      p = text.find(op)
      if (p >= 0) && ((op_pos < 0) || (p < op_pos))
        op_pos = p
        op_txt = op
      end
    end
    if op_pos < 0
      return nil
    end
    left = __pytra_slice(text, 0, op_pos).strip()
    right = __pytra_slice(text, op_pos + __pytra_len(op_txt), __pytra_len(text)).strip()
    if (right == "") || (!_is_dotted_ident(left))
      return nil
    end
    return Match.new(text, [left, op_txt, right])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"
    eq = text.find("=")
    if eq < 0
      return nil
    end
    left = __pytra_slice(text, 0, eq)
    right = __pytra_slice(text, eq + 1, __pytra_len(text)).strip()
    if right == ""
      return nil
    end
    c = left.find(",")
    if c < 0
      return nil
    end
    a = __pytra_slice(left, 0, c).strip()
    b = __pytra_slice(left, c + 1, __pytra_len(left)).strip()
    if (!_is_ident(a)) || (!_is_ident(b))
      return nil
    end
    return Match.new(text, [a, b, right])
  end
  if pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$"
    t = _strip_suffix_colon(text)
    if t == ""
      return nil
    end
    rest = t.strip()
    if !__pytra_truthy(rest.startswith("if"))
      return nil
    end
    rest = __pytra_slice(rest, 2, __pytra_len(rest)).strip()
    if !__pytra_truthy(rest.startswith("__name__"))
      return nil
    end
    rest = __pytra_slice(rest, __pytra_len("__name__"), __pytra_len(rest)).strip()
    if !__pytra_truthy(rest.startswith("=="))
      return nil
    end
    rest = __pytra_slice(rest, 2, __pytra_len(rest)).strip()
    if __pytra_contains(nil, rest)
      return Match.new(text, [])
    end
    return nil
  end
  if pattern == "^import\\s+(.+)$"
    if !__pytra_truthy(text.startswith("import"))
      return nil
    end
    if __pytra_len(text) <= 6
      return nil
    end
    if !_is_space_ch(__pytra_slice(text, 6, 7))
      return nil
    end
    rest = __pytra_slice(text, 7, __pytra_len(text)).strip()
    if rest == ""
      return nil
    end
    return Match.new(text, [rest])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"
    parts = text.split(" as ")
    if __pytra_len(parts) == 1
      name = __pytra_get_index(parts, 0).strip()
      if !_is_dotted_ident(name)
        return nil
      end
      return Match.new(text, [name, ""])
    end
    if __pytra_len(parts) == 2
      name = __pytra_get_index(parts, 0).strip()
      alias_ = __pytra_get_index(parts, 1).strip()
      if (!_is_dotted_ident(name)) || (!_is_ident(alias_))
        return nil
      end
      return Match.new(text, [name, alias_])
    end
    return nil
  end
  if pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$"
    if !__pytra_truthy(text.startswith("from "))
      return nil
    end
    rest = __pytra_slice(text, 5, __pytra_len(text))
    i = rest.find(" import ")
    if i < 0
      return nil
    end
    mod = __pytra_slice(rest, 0, i).strip()
    sym = __pytra_slice(rest, i + 8, __pytra_len(rest)).strip()
    if (!_is_dotted_ident(mod)) || (sym == "")
      return nil
    end
    return Match.new(text, [mod, sym])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"
    parts = text.split(" as ")
    if __pytra_len(parts) == 1
      name = __pytra_get_index(parts, 0).strip()
      if !_is_ident(name)
        return nil
      end
      return Match.new(text, [name, ""])
    end
    if __pytra_len(parts) == 2
      name = __pytra_get_index(parts, 0).strip()
      alias_ = __pytra_get_index(parts, 1).strip()
      if (!_is_ident(name)) || (!_is_ident(alias_))
        return nil
      end
      return Match.new(text, [name, alias_])
    end
    return nil
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"
    c = text.find(":")
    if c <= 0
      return nil
    end
    name = __pytra_slice(text, 0, c).strip()
    rhs = __pytra_slice(text, c + 1, __pytra_len(text))
    eq = rhs.find("=")
    if eq < 0
      return nil
    end
    ann = __pytra_slice(rhs, 0, eq).strip()
    expr = __pytra_slice(rhs, eq + 1, __pytra_len(rhs)).strip()
    if (!_is_ident(name)) || (ann == "") || (expr == "")
      return nil
    end
    return Match.new(text, [name, ann, expr])
  end
  if pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"
    eq = text.find("=")
    if eq < 0
      return nil
    end
    name = __pytra_slice(text, 0, eq).strip()
    expr = __pytra_slice(text, eq + 1, __pytra_len(text)).strip()
    if (!_is_ident(name)) || (expr == "")
      return nil
    end
    return Match.new(text, [name, expr])
  end
  raise RuntimeError, __pytra_str(nil)
end

def sub(pattern, repl, text, flags)
  if pattern == "\\s+"
    out = []
    in_ws = false
    for ch in __pytra_as_list(text)
      if __pytra_truthy(ch.isspace())
        if !in_ws
          out.append(repl)
          in_ws = true
        end
      else
        out.append(ch)
        in_ws = false
      end
    end
    return "".join(out)
  end
  if pattern == "\\s+#.*$"
    i = 0
    while i < __pytra_len(text)
      if __pytra_truthy(__pytra_get_index(text, i).isspace())
        j = i + 1
        while (j < __pytra_len(text)) && __pytra_truthy(__pytra_get_index(text, j).isspace())
          j += 1
        end
        if (j < __pytra_len(text)) && (__pytra_get_index(text, j) == "#")
          return __pytra_slice(text, 0, i) + repl
        end
      end
      i += 1
    end
    return text
  end
  if pattern == "[^0-9A-Za-z_]"
    out = []
    for ch in __pytra_as_list(text)
      if __pytra_truthy(ch.isalnum()) || (ch == "_")
        out.append(ch)
      else
        out.append(repl)
      end
    end
    return "".join(out)
  end
  raise RuntimeError, __pytra_str(nil)
end

if __FILE__ == $PROGRAM_NAME
end
