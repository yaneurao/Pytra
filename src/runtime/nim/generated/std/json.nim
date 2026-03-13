# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/json.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure Python JSON utilities for selfhost-friendly transpilation."
var vEMPTY: string = ""
var vCOMMA_NL: string = ",\n"
var vHEX_DIGITS: string = "0123456789abcdef"
proc vis_ws*(ch: string): bool =
  return ((ch == " ") or (ch == "	") or (ch == "") or (ch == "\n"))

proc vis_digit*(ch: string): bool =
  return ((ch >= "0") and (ch <= "9"))

proc vhex_value*(ch: string): int =
  if py_truthy(((ch >= "0") and (ch <= "9"))):
    return parseInt(ch)
  if py_truthy(((ch == "a") or (ch == "A"))):
    return 10
  if py_truthy(((ch == "b") or (ch == "B"))):
    return 11
  if py_truthy(((ch == "c") or (ch == "C"))):
    return 12
  if py_truthy(((ch == "d") or (ch == "D"))):
    return 13
  if py_truthy(((ch == "e") or (ch == "E"))):
    return 14
  if py_truthy(((ch == "f") or (ch == "F"))):
    return 15
  raise newException(Exception, "invalid json unicode escape")

proc vint_from_hex4*(hx: string): int =
  var v0: int = 0
  var v1: int = 0
  var v2: int = 0
  var v3: int = 0
  if (hx.len != 4):
    raise newException(Exception, "invalid json unicode escape")
  v0 = vhex_value(hx[0 ..< 1])
  v1 = vhex_value(hx[1 ..< 2])
  v2 = vhex_value(hx[2 ..< 3])
  v3 = vhex_value(hx[3 ..< 4])
  return ((((v0 * 4096) + (v1 * 256)) + (v2 * 16)) + v3)

proc vhex4*(code: int): string =
  var d0: int = 0
  var d1: int = 0
  var d2: int = 0
  var d3: int = 0
  var p0: string = ""
  var p1: string = ""
  var p2: string = ""
  var p3: string = ""
  var v: int = 0
  v = py_mod(int(code), int(65536))
  d3 = py_mod(int(v), int(16))
  v = (v div 16)
  d2 = py_mod(int(v), int(16))
  v = (v div 16)
  d1 = py_mod(int(v), int(16))
  v = (v div 16)
  d0 = py_mod(int(v), int(16))
  p0 = vHEX_DIGITS[d0 ..< (d0 + 1)] # string
  p1 = vHEX_DIGITS[d1 ..< (d1 + 1)] # string
  p2 = vHEX_DIGITS[d2 ..< (d2 + 1)] # string
  p3 = vHEX_DIGITS[d3 ..< (d3 + 1)] # string
  return ($(($(($(p0) & $(p1))) & $(p2))) & $(p3))

proc vjson_array_items*(raw: auto): seq[auto] =
  return list(raw)

proc vjson_new_array*(): seq[auto] =
  return list()

proc vjson_obj_require*(raw: Table[string, auto], key: string): auto =
  for it in raw.items():
    if (k == key):
      return value
  raise newException(Exception, ($("json object key not found: ") & $(key)))

proc vjson_indent_value*(indent: auto): int =
  var indent_i: int = 0
  if (indent == nil):
    raise newException(Exception, "json indent is required")
  indent_i = indent # int
  return indent_i

type JsonObj* = ref object
  raw*: Table[string, auto]

proc get*(self: JsonObj, key: string): JsonValue
proc get_obj*(self: JsonObj, key: string)
proc get_arr*(self: JsonObj, key: string)
proc get_str*(self: JsonObj, key: string)
proc get_int*(self: JsonObj, key: string)
proc get_float*(self: JsonObj, key: string)
proc get_bool*(self: JsonObj, key: string)

proc newJsonObj*(raw: Table[string, auto]): JsonObj =
  new(result)
  result.raw = raw

proc get*(self: JsonObj, key: string): JsonValue =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value)

proc get_obj*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_obj()

proc get_arr*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_arr()

proc get_str*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_str()

proc get_int*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_int()

proc get_float*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_float()

proc get_bool*(self: JsonObj, key: string): auto =
  if (not hasKey(self.raw, key)):
    return nil
  var value = vjson_obj_require(self.raw, key)
  return newJsonValue(value).as_bool()

type JsonArr* = ref object
  raw*: seq[auto]

proc get*(self: JsonArr, index: int): JsonValue
proc get_obj*(self: JsonArr, index: int)
proc get_arr*(self: JsonArr, index: int)
proc get_str*(self: JsonArr, index: int)
proc get_int*(self: JsonArr, index: int)
proc get_float*(self: JsonArr, index: int)
proc get_bool*(self: JsonArr, index: int)

proc newJsonArr*(raw: seq[auto]): JsonArr =
  new(result)
  result.raw = raw

proc get*(self: JsonArr, index: int): JsonValue =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index])

proc get_obj*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_obj()

proc get_arr*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_arr()

proc get_str*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_str()

proc get_int*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_int()

proc get_float*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_float()

proc get_bool*(self: JsonArr, index: int): auto =
  if py_truthy(((index < 0) or (index >= vjson_array_items(self.raw).len))):
    return nil
  return newJsonValue(vjson_array_items(self.raw)[index]).as_bool()

type JsonValue* = ref object
  raw*: int

proc as_obj*(self: JsonValue): JsonObj
proc as_arr*(self: JsonValue): JsonArr
proc as_str*(self: JsonValue)
proc as_int*(self: JsonValue): int
proc as_float*(self: JsonValue): float
proc as_bool*(self: JsonValue): bool

proc newJsonValue*(raw: auto): JsonValue =
  new(result)
  result.raw = raw

proc as_obj*(self: JsonValue): JsonObj =
  var raw_obj: Table[string, auto] = initTable[string, int]()
  var raw = self.raw
  if py_truthy(false):
    raw_obj = dict(raw)
    return newJsonObj(raw_obj)
  return nil

proc as_arr*(self: JsonValue): JsonArr =
  var raw_arr: seq[auto] = @[]
  var raw = self.raw
  if py_truthy(false):
    raw_arr = list(raw)
    return newJsonArr(raw_arr)
  return nil

proc as_str*(self: JsonValue): auto =
  var raw = self.raw
  if py_truthy(false):
    return raw
  return nil

proc as_int*(self: JsonValue): int =
  var raw_i: int = 0
  var raw = self.raw
  if py_truthy(false):
    return nil
  if py_truthy(false):
    raw_i = int(raw)
    return raw_i
  return nil

proc as_float*(self: JsonValue): float =
  var raw_f: float = 0.0
  var raw = self.raw
  if py_truthy(false):
    raw_f = float(raw)
    return raw_f
  return nil

proc as_bool*(self: JsonValue): bool =
  var raw_b: bool = false
  var raw = self.raw
  if py_truthy(false):
    raw_b = py_truthy(raw)
    return raw_b
  return nil

type vJsonParser* = ref object
  text*: string
  n*: int
  i*: int

proc parse*(self: vJsonParser)
proc vskip_ws*(self: vJsonParser)
proc vparse_value*(self: vJsonParser): Table[string, auto]
proc vparse_object*(self: vJsonParser): Table[string, auto]
proc vparse_array*(self: vJsonParser): seq[auto]
proc vparse_string*(self: vJsonParser): string
proc vparse_number*(self: vJsonParser): float

proc newvJsonParser*(text: string): vJsonParser =
  new(result)
  result.text = text
  result.n = text.len
  result.i = 0

proc parse*(self: vJsonParser): auto =
  self.vskip_ws()
  var `out` = self.vparse_value()
  self.vskip_ws()
  if (self.i != self.n):
    raise newException(Exception, "invalid json: trailing characters")
  return `out`

proc vskip_ws*(self: vJsonParser) =
  while py_truthy(((self.i < self.n) and py_truthy(vis_ws($(self.text[self.i]))))):
    self.i += 1

proc vparse_value*(self: vJsonParser): Table[string, auto] =
  var ch: string = ""
  if (self.i >= self.n):
    raise newException(Exception, "invalid json: unexpected end")
  ch = $(self.text[self.i])
  if (ch == "{"):
    return self.vparse_object()
  if (ch == "["):
    return self.vparse_array()
  if (ch == "\""):
    return self.vparse_string()
  if py_truthy(((ch == "t") and (self.text[self.i ..< (self.i + 4)] == "true"))):
    self.i += 4
    return true
  if py_truthy(((ch == "f") and (self.text[self.i ..< (self.i + 5)] == "false"))):
    self.i += 5
    return false
  if py_truthy(((ch == "n") and (self.text[self.i ..< (self.i + 4)] == "null"))):
    self.i += 4
    return nil
  return self.vparse_number()

proc vparse_object*(self: vJsonParser): Table[string, auto] =
  var `out`: Table[string, auto] = initTable[string, int]()
  var ch: string = ""
  var key: string = ""
  `out` = initTable[string, int]() # Table[string, auto]
  self.i += 1
  self.vskip_ws()
  if py_truthy(((self.i < self.n) and ($(self.text[self.i]) == "}"))):
    self.i += 1
    return `out`
  while true:
    self.vskip_ws()
    if py_truthy(((self.i >= self.n) or ($(self.text[self.i]) != "\""))):
      raise newException(Exception, "invalid json object key")
    key = self.vparse_string()
    self.vskip_ws()
    if py_truthy(((self.i >= self.n) or ($(self.text[self.i]) != ":"))):
      raise newException(Exception, "invalid json object: missing ':'")
    self.i += 1
    self.vskip_ws()
    `out`[key] = self.vparse_value()
    self.vskip_ws()
    if (self.i >= self.n):
      raise newException(Exception, "invalid json object: unexpected end")
    ch = $(self.text[self.i])
    self.i += 1
    if (ch == "}"):
      return `out`
    if (ch != ","):
      raise newException(Exception, "invalid json object separator")

proc vparse_array*(self: vJsonParser): seq[auto] =
  var `out`: seq[auto] = @[]
  var ch: string = ""
  `out` = vjson_new_array()
  self.i += 1
  self.vskip_ws()
  if py_truthy(((self.i < self.n) and ($(self.text[self.i]) == "]"))):
    self.i += 1
    return `out`
  while true:
    self.vskip_ws()
    `out`.add(self.vparse_value())
    self.vskip_ws()
    if (self.i >= self.n):
      raise newException(Exception, "invalid json array: unexpected end")
    ch = $(self.text[self.i])
    self.i += 1
    if (ch == "]"):
      return `out`
    if (ch != ","):
      raise newException(Exception, "invalid json array separator")

proc vparse_string*(self: vJsonParser): string =
  var ch: string = ""
  var esc: string = ""
  var hx: string = ""
  var out_chars: seq[string] = @[]
  if ($(self.text[self.i]) != "\""):
    raise newException(Exception, "invalid json string")
  self.i += 1
  out_chars = @[] # seq[string]
  while (self.i < self.n):
    ch = $(self.text[self.i])
    self.i += 1
    if (ch == "\""):
      return vjoin_strs(out_chars, vEMPTY)
    if (ch == "\\"):
      if (self.i >= self.n):
        raise newException(Exception, "invalid json string escape")
      esc = $(self.text[self.i])
      self.i += 1
      if (esc == "\""):
        out_chars.add("\"")
      elif (esc == "\\"):
        out_chars.add("\\")
      elif (esc == "/"):
        out_chars.add("/")
      elif (esc == "b"):
        out_chars.add("")
      elif (esc == "f"):
        out_chars.add("")
      elif (esc == "n"):
        out_chars.add("\n")
      elif (esc == "r"):
        out_chars.add("")
      elif (esc == "t"):
        out_chars.add("	")
      elif (esc == "u"):
        if ((self.i + 4) > self.n):
          raise newException(Exception, "invalid json unicode escape")
        hx = self.text[self.i ..< (self.i + 4)]
        self.i += 4
        out_chars.add(chr(vint_from_hex4(hx)))
      else:
        raise newException(Exception, "invalid json escape")
    else:
      out_chars.add(ch)
  raise newException(Exception, "unterminated json string")

proc vparse_number*(self: vJsonParser): float =
  var exp_ch: string = ""
  var is_float: bool = false
  var num_f: float = 0.0
  var num_i: int = 0
  var sign: string = ""
  var start: int = 0
  var token: string = ""
  start = self.i
  if ($(self.text[self.i]) == "-"):
    self.i += 1
  if (self.i >= self.n):
    raise newException(Exception, "invalid json number")
  if ($(self.text[self.i]) == "0"):
    self.i += 1
  else:
    if py_truthy((not py_truthy(vis_digit($(self.text[self.i]))))):
      raise newException(Exception, "invalid json number")
    while py_truthy(((self.i < self.n) and py_truthy(vis_digit($(self.text[self.i]))))):
      self.i += 1
  is_float = false
  if py_truthy(((self.i < self.n) and ($(self.text[self.i]) == "."))):
    is_float = true
    self.i += 1
    if py_truthy(((self.i >= self.n) or py_truthy((not py_truthy(vis_digit($(self.text[self.i]))))))):
      raise newException(Exception, "invalid json number")
    while py_truthy(((self.i < self.n) and py_truthy(vis_digit($(self.text[self.i]))))):
      self.i += 1
  if (self.i < self.n):
    exp_ch = $(self.text[self.i])
    if py_truthy(((exp_ch == "e") or (exp_ch == "E"))):
      is_float = true
      self.i += 1
      if (self.i < self.n):
        sign = $(self.text[self.i])
        if py_truthy(((sign == "+") or (sign == "-"))):
          self.i += 1
      if py_truthy(((self.i >= self.n) or py_truthy((not py_truthy(vis_digit($(self.text[self.i]))))))):
        raise newException(Exception, "invalid json exponent")
      while py_truthy(((self.i < self.n) and py_truthy(vis_digit($(self.text[self.i]))))):
        self.i += 1
  token = self.text[start ..< self.i]
  if py_truthy(is_float):
    num_f = parseFloat(token)
    return num_f
  num_i = parseInt(token) # int
  return num_i

proc loads*(text: string): auto =
  return vJsonParser(text).parse()

proc loads_obj*(text: string): JsonObj =
  var raw_obj: Table[string, auto] = initTable[string, int]()
  var value = vJsonParser(text).parse()
  if py_truthy(false):
    raw_obj = dict(value)
    return newJsonObj(raw_obj)
  return nil

proc loads_arr*(text: string): JsonArr =
  var raw_arr: seq[auto] = @[]
  var value = vJsonParser(text).parse()
  if py_truthy(false):
    raw_arr = list(value)
    return newJsonArr(raw_arr)
  return nil

proc vjoin_strs*(parts: seq[string], sep: string): string =
  var `out`: string = ""
  var i: int = 0
  if (parts.len == 0):
    return ""
  `out` = $(parts[0]) # string
  i = 1
  while (i < parts.len):
    `out` = ($(($(`out`) & $(sep))) & $($(parts[i])))
    i += 1
  return `out`

proc vescape_str*(s: string, ensure_ascii: bool): string =
  var `out`: seq[string] = @[]
  var code: int = 0
  `out` = @["\""] # seq[string]
  for ch in s:
    code = ord(ch)
    if (ch == "\""):
      `out`.add("\\\"")
    elif (ch == "\\"):
      `out`.add("\\\\")
    elif (ch == ""):
      `out`.add("\\b")
    elif (ch == ""):
      `out`.add("\\f")
    elif (ch == "\n"):
      `out`.add("\\n")
    elif (ch == ""):
      `out`.add("\\r")
    elif (ch == "	"):
      `out`.add("\\t")
    elif py_truthy((py_truthy(ensure_ascii) and (code > 127))):
      `out`.add(($("\\u") & $(vhex4(code))))
    else:
      `out`.add(ch)
  `out`.add("\"")
  return vjoin_strs(`out`, vEMPTY)

proc vdump_json_list*(values: seq[auto], ensure_ascii: bool, indent: auto, item_sep: string, key_sep: string, level: int): string =
  var dumped: seq[string] = @[]
  var dumped_txt: string = ""
  var indent_i: int = 0
  var inner: seq[string] = @[]
  var prefix: string = ""
  var value_txt: string = ""
  if (values.len == 0):
    return "[]"
  if (indent == nil):
    dumped = @[]
    for x in values:
      dumped_txt = vdump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
      dumped.add(dumped_txt)
    return ($(($("[") & $(vjoin_strs(dumped, item_sep)))) & $("]"))
  indent_i = vjson_indent_value(indent) # int
  inner = @[] # seq[string]
  for x in values:
    prefix = (" " * (indent_i * (level + 1)))
    value_txt = vdump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1))
    inner.add(($(prefix) & $(value_txt)))
  return ($(($(($(($("[\n") & $(vjoin_strs(inner, vCOMMA_NL)))) & $("\n"))) & $((" " * (indent_i * level))))) & $("]"))

proc vdump_json_dict*(values: Table[string, auto], ensure_ascii: bool, indent: auto, item_sep: string, key_sep: string, level: int): string =
  var indent_i: int = 0
  var inner: seq[string] = @[]
  var k_txt: string = ""
  var parts: seq[string] = @[]
  var prefix: string = ""
  var v_txt: string = ""
  if (values.len == 0):
    return "{}"
  if (indent == nil):
    parts = @[]
    for it in values.items():
      k_txt = vescape_str($(k), ensure_ascii)
      v_txt = vdump_json_value(x, ensure_ascii, indent, item_sep, key_sep, level)
      parts.add(($(($(k_txt) & $(key_sep))) & $(v_txt)))
    return ($(($("{") & $(vjoin_strs(parts, item_sep)))) & $("}"))
  indent_i = vjson_indent_value(indent) # int
  inner = @[] # seq[string]
  for it in values.items():
    prefix = (" " * (indent_i * (level + 1)))
    k_txt = vescape_str($(k), ensure_ascii)
    v_txt = vdump_json_value(x, ensure_ascii, indent, item_sep, key_sep, (level + 1))
    inner.add(($(($(($(prefix) & $(k_txt))) & $(key_sep))) & $(v_txt)))
  return ($(($(($(($("{\n") & $(vjoin_strs(inner, vCOMMA_NL)))) & $("\n"))) & $((" " * (indent_i * level))))) & $("}"))

proc vdump_json_value*(v: auto, ensure_ascii: bool, indent: auto, item_sep: string, key_sep: string, level: int): string =
  var as_dict: Table[string, auto] = initTable[string, int]()
  var as_list: seq[auto] = @[]
  var raw_b: bool = false
  if (v == nil):
    return "null"
  if py_truthy(false):
    raw_b = py_truthy(v)
    return (if py_truthy(raw_b): "true" else: "false")
  if py_truthy(false):
    return $(v)
  if py_truthy(false):
    return $(v)
  if py_truthy(false):
    return vescape_str(v, ensure_ascii)
  if py_truthy(false):
    as_list = list(v)
    return vdump_json_list(as_list, ensure_ascii, indent, item_sep, key_sep, level)
  if py_truthy(false):
    as_dict = dict(v)
    return vdump_json_dict(as_dict, ensure_ascii, indent, item_sep, key_sep, level)
  raise newException(Exception, "json.dumps unsupported type")

proc dumps*(obj: auto, ensure_ascii: bool, indent: auto, separators: (string, auto)): string =
  var item_sep: string = ""
  var key_sep: string = ""
  item_sep = ","
  key_sep = (if (indent == nil): ":" else: ": ")
  if (separators == nil):
    (item_sep, key_sep) = separators
  return vdump_json_value(obj, ensure_ascii, indent, item_sep, key_sep, 0)
