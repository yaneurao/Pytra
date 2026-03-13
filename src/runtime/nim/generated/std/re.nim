# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/re.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Minimal pure-Python regex subset used by Pytra selfhost path."
var S = 1
type Match* = ref object
  vtext*: string
  vgroups*: seq[string]

proc group*(self: Match, idx: int): string

proc newMatch*(text: string, groups: seq[string]): Match =
  new(result)
  result.vtext = text
  result.vgroups = groups

proc group*(self: Match, idx: int): string =
  if (idx == 0):
    return self.vtext
  if py_truthy(((idx < 0) or (idx > self.vgroups.len))):
    raise newException(Exception, IndexError("group index out of range"))
  return $(self.vgroups[(idx - 1)])

proc group*(m: auto, idx: int): string =
  var mm: Match = nil
  if (m == nil):
    return ""
  mm = m # Match
  return mm.group(idx)

proc strip_group*(m: auto, idx: int): string =
  return group(m, idx).strip()

proc vis_ident*(s: string): bool =
  var h: string = ""
  var is_alpha: bool = false
  var is_digit: bool = false
  var is_head_alpha: bool = false
  if (s == ""):
    return false
  h = s[0 ..< 1]
  is_head_alpha = (("a" <= h) or ("A" <= h))
  if py_truthy((not py_truthy((py_truthy(is_head_alpha) or (h == "_"))))):
    return false
  for ch in s[1 ..< (s.len)]:
    is_alpha = (("a" <= ch) or ("A" <= ch))
    is_digit = ("0" <= ch)
    if py_truthy((not py_truthy((py_truthy(is_alpha) or py_truthy(is_digit) or (ch == "_"))))):
      return false
  return true

proc vis_dotted_ident*(s: string): bool =
  var part: string = ""
  if (s == ""):
    return false
  part = ""
  for ch in s:
    if (ch == "."):
      if py_truthy((not py_truthy(vis_ident(part)))):
        return false
      part = ""
      continue
    part += ch
  if py_truthy((not py_truthy(vis_ident(part)))):
    return false
  if (part == ""):
    return false
  return true

proc vstrip_suffix_colon*(s: string): string =
  var t: string = ""
  t = s.rstrip()
  if (t.len == 0):
    return ""
  if (t[(-1) ..< (t.len)] != ":"):
    return ""
  return t[0 ..< (-1)]

proc vis_space_ch*(ch: string): bool =
  if (ch == " "):
    return true
  if (ch == "	"):
    return true
  if (ch == ""):
    return true
  if (ch == "\n"):
    return true
  return false

proc vis_alnum_or_underscore*(ch: string): bool =
  var is_alpha: bool = false
  var is_digit: bool = false
  is_alpha = (("a" <= ch) or ("A" <= ch))
  is_digit = ("0" <= ch)
  if py_truthy((py_truthy(is_alpha) or py_truthy(is_digit))):
    return true
  return (ch == "_")

proc vskip_spaces*(t: string, i: int): int =
  while (i < t.len):
    if py_truthy((not py_truthy(vis_space_ch(t[i ..< (i + 1)])))):
      return i
    i += 1
  return i

proc match*(pattern: string, text: string, flags: int): Match =
  var `mod`: string = ""
  var `var`: string = ""
  var a: string = ""
  var alias: string = ""
  var ann: string = ""
  var args: string = ""
  var b: string = ""
  var base: string = ""
  var c: int = 0
  var eq: int = 0
  var exc: string = ""
  var expr: string = ""
  var head: string = ""
  var i: int = 0
  var inner: string = ""
  var it: string = ""
  var j: int = 0
  var k: int = 0
  var left: string = ""
  var m1: string = ""
  var m2: string = ""
  var name: string = ""
  var op_pos: int = 0
  var op_txt: string = ""
  var ops: seq[string] = @[]
  var parts: seq[string] = @[]
  var r: int = 0
  var rest: string = ""
  var ret: string = ""
  var rhs: string = ""
  var right: string = ""
  var sym: string = ""
  var t: string = ""
  var tail: string = ""
  var target: string = ""
  var val: string = ""
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\[(.*)\\]$"):
    if py_truthy((not py_truthy(text.endswith("]")))):
      return nil
    i = text.find("[")
    if (i <= 0):
      return nil
    head = text[0 ..< i]
    if py_truthy((not py_truthy(vis_ident(head)))):
      return nil
    return newMatch(text, @[head, text[(i + 1) ..< (-1)]])
  if (pattern == "^def\\s+([A-Za-z_][A-Za-z0-9_]*)\\((.*)\\)\\s*(?:->\\s*(.+)\\s*)?:\\s*$"):
    t = vstrip_suffix_colon(text)
    if (t == ""):
      return nil
    i = 0
    if py_truthy((not py_truthy(t.startswith("def")))):
      return nil
    i = 3
    if py_truthy(((i >= t.len) or py_truthy((not py_truthy(vis_space_ch(t[i ..< (i + 1)])))))):
      return nil
    i = vskip_spaces(t, i)
    j = i
    while py_truthy(((j < t.len) and py_truthy(vis_alnum_or_underscore(t[j ..< (j + 1)])))):
      j += 1
    name = t[i ..< j]
    if py_truthy((not py_truthy(vis_ident(name)))):
      return nil
    k = j
    k = vskip_spaces(t, k)
    if py_truthy(((k >= t.len) or (t[k ..< (k + 1)] != "("))):
      return nil
    r = t.rfind(")")
    if (r <= k):
      return nil
    args = t[(k + 1) ..< r]
    tail = t[(r + 1) ..< (t.len)].strip()
    if (tail == ""):
      return newMatch(text, @[name, args, ""])
    if py_truthy((not py_truthy(tail.startswith("->")))):
      return nil
    ret = tail[2 ..< (tail.len)].strip()
    if (ret == ""):
      return nil
    return newMatch(text, @[name, args, ret])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)(?:\\s*=\\s*(.+))?$"):
    c = text.find(":")
    if (c <= 0):
      return nil
    name = text[0 ..< c].strip()
    if py_truthy((not py_truthy(vis_ident(name)))):
      return nil
    rhs = text[(c + 1) ..< (text.len)]
    eq = rhs.find("=")
    if (eq < 0):
      ann = rhs.strip()
      if (ann == ""):
        return nil
      return newMatch(text, @[name, ann, ""])
    ann = rhs[0 ..< eq].strip()
    val = rhs[(eq + 1) ..< (rhs.len)].strip()
    if py_truthy(((ann == "") or (val == ""))):
      return nil
    return newMatch(text, @[name, ann, val])
  if (pattern == "^[A-Za-z_][A-Za-z0-9_]*$"):
    if py_truthy(vis_ident(text)):
      return newMatch(text, @[])
    return nil
  if (pattern == "^class\\s+([A-Za-z_][A-Za-z0-9_]*)(?:\\(([A-Za-z_][A-Za-z0-9_]*)\\))?\\s*:\\s*$"):
    t = vstrip_suffix_colon(text)
    if (t == ""):
      return nil
    if py_truthy((not py_truthy(t.startswith("class")))):
      return nil
    i = 5
    if py_truthy(((i >= t.len) or py_truthy((not py_truthy(vis_space_ch(t[i ..< (i + 1)])))))):
      return nil
    i = vskip_spaces(t, i)
    j = i
    while py_truthy(((j < t.len) and py_truthy(vis_alnum_or_underscore(t[j ..< (j + 1)])))):
      j += 1
    name = t[i ..< j]
    if py_truthy((not py_truthy(vis_ident(name)))):
      return nil
    tail = t[j ..< (t.len)].strip()
    if (tail == ""):
      return newMatch(text, @[name, ""])
    if py_truthy((not py_truthy((py_truthy(tail.startswith("(")) and py_truthy(tail.endswith(")")))))):
      return nil
    base = tail[1 ..< (-1)].strip()
    if py_truthy((not py_truthy(vis_ident(base)))):
      return nil
    return newMatch(text, @[name, base])
  if (pattern == "^(any|all)\\((.+)\\)$"):
    if py_truthy((py_truthy(text.startswith("any(")) and py_truthy(text.endswith(")")) and (text.len > 5))):
      return newMatch(text, @["any", text[4 ..< (-1)]])
    if py_truthy((py_truthy(text.startswith("all(")) and py_truthy(text.endswith(")")) and (text.len > 5))):
      return newMatch(text, @["all", text[4 ..< (-1)]])
    return nil
  if (pattern == "^\\[\\s*([A-Za-z_][A-Za-z0-9_]*)\\s+for\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+in\\s+(.+)\\]$"):
    if py_truthy((not py_truthy((py_truthy(text.startswith("[")) and py_truthy(text.endswith("]")))))):
      return nil
    inner = text[1 ..< (-1)].strip()
    m1 = " for "
    m2 = " in "
    i = inner.find(m1)
    if (i < 0):
      return nil
    expr = inner[0 ..< i].strip()
    rest = inner[(i + m1.len) ..< (inner.len)]
    j = rest.find(m2)
    if (j < 0):
      return nil
    `var` = rest[0 ..< j].strip()
    it = rest[(j + m2.len) ..< (rest.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_ident(expr)))) or py_truthy((not py_truthy(vis_ident(`var`)))) or (it == ""))):
      return nil
    return newMatch(text, @[expr, `var`, it])
  if (pattern == "^for\\s+(.+)\\s+in\\s+(.+):$"):
    t = vstrip_suffix_colon(text)
    if py_truthy(((t == "") or py_truthy((not py_truthy(t.startswith("for")))))):
      return nil
    rest = t[3 ..< (t.len)].strip()
    i = rest.find(" in ")
    if (i < 0):
      return nil
    left = rest[0 ..< i].strip()
    right = rest[(i + 4) ..< (rest.len)].strip()
    if py_truthy(((left == "") or (right == ""))):
      return nil
    return newMatch(text, @[left, right])
  if (pattern == "^with\\s+(.+)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"):
    t = vstrip_suffix_colon(text)
    if py_truthy(((t == "") or py_truthy((not py_truthy(t.startswith("with")))))):
      return nil
    rest = t[4 ..< (t.len)].strip()
    i = rest.rfind(" as ")
    if (i < 0):
      return nil
    expr = rest[0 ..< i].strip()
    name = rest[(i + 4) ..< (rest.len)].strip()
    if py_truthy(((expr == "") or py_truthy((not py_truthy(vis_ident(name)))))):
      return nil
    return newMatch(text, @[expr, name])
  if (pattern == "^except\\s+(.+?)\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*$"):
    t = vstrip_suffix_colon(text)
    if py_truthy(((t == "") or py_truthy((not py_truthy(t.startswith("except")))))):
      return nil
    rest = t[6 ..< (t.len)].strip()
    i = rest.rfind(" as ")
    if (i < 0):
      return nil
    exc = rest[0 ..< i].strip()
    name = rest[(i + 4) ..< (rest.len)].strip()
    if py_truthy(((exc == "") or py_truthy((not py_truthy(vis_ident(name)))))):
      return nil
    return newMatch(text, @[exc, name])
  if (pattern == "^except\\s+(.+?)\\s*:\\s*$"):
    t = vstrip_suffix_colon(text)
    if py_truthy(((t == "") or py_truthy((not py_truthy(t.startswith("except")))))):
      return nil
    rest = t[6 ..< (t.len)].strip()
    if (rest == ""):
      return nil
    return newMatch(text, @[rest])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*(.+)$"):
    c = text.find(":")
    if (c <= 0):
      return nil
    target = text[0 ..< c].strip()
    ann = text[(c + 1) ..< (text.len)].strip()
    if py_truthy(((ann == "") or py_truthy((not py_truthy(vis_dotted_ident(target)))))):
      return nil
    return newMatch(text, @[target, ann])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"):
    c = text.find(":")
    if (c <= 0):
      return nil
    target = text[0 ..< c].strip()
    rhs = text[(c + 1) ..< (text.len)]
    eq = rhs.find("=")
    if (eq < 0):
      return nil
    ann = rhs[0 ..< eq].strip()
    expr = rhs[(eq + 1) ..< (rhs.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_dotted_ident(target)))) or (ann == "") or (expr == ""))):
      return nil
    return newMatch(text, @[target, ann, expr])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z_][A-Za-z0-9_]*)?)\\s*(\\+=|-=|\\*=|/=|//=|%=|&=|\\|=|\\^=|<<=|>>=)\\s*(.+)$"):
    ops = @["<<=", ">>=", "+=", "-=", "*=", "/=", "//=", "%=", "&=", "|=", "^="]
    op_pos = (-1)
    op_txt = ""
    for op in ops:
      var p = text.find(op)
      if py_truthy(((p >= 0) and py_truthy(((op_pos < 0) or (p < op_pos))))):
        op_pos = p
        op_txt = op
    if (op_pos < 0):
      return nil
    left = text[0 ..< op_pos].strip()
    right = text[(op_pos + op_txt.len) ..< (text.len)].strip()
    if py_truthy(((right == "") or py_truthy((not py_truthy(vis_dotted_ident(left)))))):
      return nil
    return newMatch(text, @[left, op_txt, right])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"):
    eq = text.find("=")
    if (eq < 0):
      return nil
    left = text[0 ..< eq]
    right = text[(eq + 1) ..< (text.len)].strip()
    if (right == ""):
      return nil
    c = left.find(",")
    if (c < 0):
      return nil
    a = left[0 ..< c].strip()
    b = left[(c + 1) ..< (left.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_ident(a)))) or py_truthy((not py_truthy(vis_ident(b)))))):
      return nil
    return newMatch(text, @[a, b, right])
  if (pattern == "^if\\s+__name__\\s*==\\s*[\\\"']__main__[\\\"']\\s*:\\s*$"):
    t = vstrip_suffix_colon(text)
    if (t == ""):
      return nil
    rest = t.strip()
    if py_truthy((not py_truthy(rest.startswith("if")))):
      return nil
    rest = rest[2 ..< (rest.len)].strip()
    if py_truthy((not py_truthy(rest.startswith("__name__")))):
      return nil
    rest = rest["__name__".len ..< (rest.len)].strip()
    if py_truthy((not py_truthy(rest.startswith("==")))):
      return nil
    rest = rest[2 ..< (rest.len)].strip()
    if (rest in 0):
      return newMatch(text, @[])
    return nil
  if (pattern == "^import\\s+(.+)$"):
    if py_truthy((not py_truthy(text.startswith("import")))):
      return nil
    if (text.len <= 6):
      return nil
    if py_truthy((not py_truthy(vis_space_ch(text[6 ..< 7])))):
      return nil
    rest = text[7 ..< (text.len)].strip()
    if (rest == ""):
      return nil
    return newMatch(text, @[rest])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_\\.]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"):
    parts = text.split(" as ")
    if (parts.len == 1):
      name = $(parts[0]).strip()
      if py_truthy((not py_truthy(vis_dotted_ident(name)))):
        return nil
      return newMatch(text, @[name, ""])
    if (parts.len == 2):
      name = $(parts[0]).strip()
      alias = $(parts[1]).strip()
      if py_truthy((py_truthy((not py_truthy(vis_dotted_ident(name)))) or py_truthy((not py_truthy(vis_ident(alias)))))):
        return nil
      return newMatch(text, @[name, alias])
    return nil
  if (pattern == "^from\\s+([A-Za-z_][A-Za-z0-9_\\.]*)\\s+import\\s+(.+)$"):
    if py_truthy((not py_truthy(text.startswith("from ")))):
      return nil
    rest = text[5 ..< (text.len)]
    i = rest.find(" import ")
    if (i < 0):
      return nil
    `mod` = rest[0 ..< i].strip()
    sym = rest[(i + 8) ..< (rest.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_dotted_ident(`mod`)))) or (sym == ""))):
      return nil
    return newMatch(text, @[`mod`, sym])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)(?:\\s+as\\s+([A-Za-z_][A-Za-z0-9_]*))?$"):
    parts = text.split(" as ")
    if (parts.len == 1):
      name = $(parts[0]).strip()
      if py_truthy((not py_truthy(vis_ident(name)))):
        return nil
      return newMatch(text, @[name, ""])
    if (parts.len == 2):
      name = $(parts[0]).strip()
      alias = $(parts[1]).strip()
      if py_truthy((py_truthy((not py_truthy(vis_ident(name)))) or py_truthy((not py_truthy(vis_ident(alias)))))):
        return nil
      return newMatch(text, @[name, alias])
    return nil
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*:\\s*([^=]+?)\\s*=\\s*(.+)$"):
    c = text.find(":")
    if (c <= 0):
      return nil
    name = text[0 ..< c].strip()
    rhs = text[(c + 1) ..< (text.len)]
    eq = rhs.find("=")
    if (eq < 0):
      return nil
    ann = rhs[0 ..< eq].strip()
    expr = rhs[(eq + 1) ..< (rhs.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_ident(name)))) or (ann == "") or (expr == ""))):
      return nil
    return newMatch(text, @[name, ann, expr])
  if (pattern == "^([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*(.+)$"):
    eq = text.find("=")
    if (eq < 0):
      return nil
    name = text[0 ..< eq].strip()
    expr = text[(eq + 1) ..< (text.len)].strip()
    if py_truthy((py_truthy((not py_truthy(vis_ident(name)))) or (expr == ""))):
      return nil
    return newMatch(text, @[name, expr])
  raise newException(Exception, 0)

proc sub*(pattern: string, repl: string, text: string, flags: int): string =
  var `out`: seq[string] = @[]
  var i: int = 0
  var in_ws: bool = false
  var j: int = 0
  if (pattern == "\\s+"):
    `out` = @[]
    in_ws = false
    for ch in text:
      if py_truthy(ch.isspace()):
        if py_truthy((not py_truthy(in_ws))):
          `out`.add(repl)
          in_ws = true
      else:
        `out`.add(ch)
        in_ws = false
    return "".join(`out`)
  if (pattern == "\\s+#.*$"):
    i = 0
    while (i < text.len):
      if py_truthy($(text[i]).isspace()):
        j = (i + 1)
        while py_truthy(((j < text.len) and py_truthy($(text[j]).isspace()))):
          j += 1
        if py_truthy(((j < text.len) and ($(text[j]) == "#"))):
          return ($(text[0 ..< i]) & $(repl))
      i += 1
    return text
  if (pattern == "[^0-9A-Za-z_]"):
    `out` = @[]
    for ch in text:
      if py_truthy((py_truthy(ch.isalnum()) or (ch == "_"))):
        `out`.add(ch)
      else:
        `out`.add(repl)
    return "".join(`out`)
  raise newException(Exception, 0)
