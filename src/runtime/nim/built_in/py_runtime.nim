# Nim runtime for Pytra
import std/os
import std/times
import std/tables
import std/strutils
import std/math
import std/sequtils
import std/sets
import std/algorithm

let py_pi*: float64 = math.PI
let py_e*: float64 = math.E

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
type PyObj* = ref object of RootObj
type PyIntObj* = ref object of PyObj
  value*: int64
type PyStrObj* = ref object of PyObj
  value*: string
type PyBoolObj* = ref object of PyObj
  value*: bool
type PyFloatObj* = ref object of PyObj
  value*: float64
type RuntimeError* = object of CatchableError
type TypeError* = object of CatchableError
type IndexError* = object of CatchableError
type SystemExit* = object of CatchableError
type PyPath* = string
type PyFile* = File

template py_instanceof*(v: typed, T: typedesc): bool =
  when T is bool:
    type(v) is bool
  elif T is string:
    type(v) is string
  elif T is int64:
    type(v) is int64 or type(v) is int
  elif T is float64:
    type(v) is float64 or type(v) is float
  elif T is SomeInteger:
    type(v) is T
  elif T is SomeFloat:
    type(v) is T
  elif compiles(v of T):
    v of T
  elif compiles(v is T):
    v is T
  else:
    false

template py_is_dict*(v: typed): bool =
  when v is Table:
    true
  else:
    false

proc py_is_list*(v: string): bool = false
proc py_is_list*[T](v: seq[T]): bool = true
proc py_is_list*[T; N: static[int]](v: array[N, T]): bool = true
proc py_is_list*[T](v: T): bool = false

template py_is_str*(v: typed): bool =
  when v is string:
    true
  else:
    false

template py_is_int*(v: typed): bool =
  when v is SomeInteger:
    true
  else:
    false

template py_is_bool*(v: typed): bool =
  when v is bool:
    true
  else:
    false

template py_is_float*(v: typed): bool =
  when v is SomeFloat:
    true
  else:
    false

proc py_open*(path: string, mode: string): PyFile =
  var f: File
  var file_mode = fmRead
  if mode == "w" or mode == "wb":
    file_mode = fmWrite
  elif mode == "a" or mode == "ab":
    file_mode = fmAppend
  elif mode == "r" or mode == "rb":
    file_mode = fmRead
  if not open(f, path, file_mode):
    raise newException(IOError, "failed to open file: " & path)
  return f

proc write*(f: var PyFile, data: seq[uint8]): int =
  if data.len > 0:
    discard writeBytes(f, data, 0, data.len)
  return data.len

proc write*(f: var PyFile, data: string): int =
  system.write(f, data)
  return data.len

proc read*(f: var PyFile): string =
  setFilePos(f, 0)
  return system.readAll(f)

proc v_enter*(f: var PyFile): PyFile =
  return f

proc v_exit*(f: var PyFile, exc_type: PyObj, exc_val: PyObj, exc_tb: PyObj) =
  close(f)

proc close*(f: var PyFile) =
  system.close(f)

proc py_to_string*(v: auto): string
proc py_box*(v: PyObj): PyObj = v
proc py_box*(v: typeof(nil)): PyObj = nil
proc py_box*(v: string): PyObj = PyStrObj(value: v)
proc py_box*(v: bool): PyObj = PyBoolObj(value: v)
proc py_box*(v: SomeInteger): PyObj = PyIntObj(value: int64(v))
proc py_box*(v: SomeFloat): PyObj = PyFloatObj(value: float64(v))

# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------
var py_capture_stdout_active = false
var py_capture_stdout_lines: seq[string] = @[]
var py_argv*: seq[string] = @[]
var py_path*: seq[string] = @[]

proc py_print*() =
  if py_capture_stdout_active:
    py_capture_stdout_lines.add("")
  else:
    echo ""

proc py_print*(args: varargs[string, py_to_string]) =
  var parts: seq[string] = @[]
  for a in args:
    parts.add(a)
  let line = parts.join(" ")
  if py_capture_stdout_active:
    py_capture_stdout_lines.add(line)
  else:
    echo line

# ---------------------------------------------------------------------------
# Conversions
# ---------------------------------------------------------------------------
proc py_perf_counter*(): float =
  epochTime()

proc py_int*(v: auto): int =
  when v is string:
    parseInt(v)
  elif v is bool:
    if v: 1 else: 0
  elif compiles(py_to_string(v)):
    let s = py_to_string(v)
    if s == "True":
      1
    elif s == "False":
      0
    elif s.contains(".") or s.contains("e") or s.contains("E"):
      int(parseFloat(s))
    else:
      parseInt(s)
  else:
    int(v)

proc py_int*(v: PyObj): int =
  if v.isNil:
    0
  elif v of PyIntObj:
    int(PyIntObj(v).value)
  elif v of PyBoolObj:
    if PyBoolObj(v).value: 1 else: 0
  elif v of PyFloatObj:
    int(PyFloatObj(v).value)
  elif v of PyStrObj:
    parseInt(PyStrObj(v).value)
  else:
    0

proc py_float*(v: auto): float =
  when v is string:
    parseFloat(v)
  else:
    float(v)

proc py_str*(v: auto): string =
  when v is PyObj:
    py_to_string(v)
  elif v is bool:
    if v: "True" else: "False"
  elif v is typeof(nil):
    "None"
  elif v is ref CatchableError:
    if v.isNil: "" else: v.msg
  elif compiles(py_to_string(v)):
    py_to_string(v)
  elif compiles($v):
    $v
  elif compiles($v[]):
    $v[]
  else:
    "<object>"

proc py_str*(v: PyObj): string =
  py_to_string(v)

proc py_to_string*(v: PyObj): string =
  if v.isNil:
    "None"
  elif v of PyStrObj:
    PyStrObj(v).value
  elif v of PyIntObj:
    $PyIntObj(v).value
  elif v of PyBoolObj:
    if PyBoolObj(v).value: "True" else: "False"
  elif v of PyFloatObj:
    $PyFloatObj(v).value
  else:
    "PyObj"

proc py_repr_item*(v: string): string = "'" & v & "'"
proc py_repr_item*(v: auto): string = py_to_string(v)

proc py_to_string*[T](v: seq[T]): string =
  var parts: seq[string] = @[]
  for item in v:
    parts.add(py_repr_item(item))
  "[" & parts.join(", ") & "]"

proc py_str*[T](v: seq[T]): string = py_to_string(v)

proc py_to_string*[K, V](v: Table[K, V]): string =
  var parts: seq[string] = @[]
  for key, value in v.pairs:
    parts.add(py_repr_item(key) & ": " & py_repr_item(value))
  "{" & parts.join(", ") & "}"

proc py_str*[K, V](v: Table[K, V]): string = py_to_string(v)

proc py_to_string*[T](v: HashSet[T]): string =
  var parts: seq[string] = @[]
  for item in v:
    parts.add(py_repr_item(item))
  "{" & parts.join(", ") & "}"

proc py_str*[T](v: HashSet[T]): string = py_to_string(v)

proc py_to_string*[A, B](v: (A, B)): string =
  "(" & py_repr_item(v[0]) & ", " & py_repr_item(v[1]) & ")"

proc py_str*[A, B](v: (A, B)): string = py_to_string(v)

proc py_to_string*[A](v: (A,)): string =
  "(" & py_repr_item(v[0]) & ",)"

proc py_str*[A](v: (A,)): string = py_to_string(v)

proc py_to_string*(v: auto): string =
  when v is PyObj:
    py_to_string(v)
  elif v is bool:
    if v: "True" else: "False"
  elif v is typeof(nil):
    "None"
  elif v is ref CatchableError:
    if v.isNil: "" else: v.msg
  elif compiles(v.pairs):
    var parts: seq[string] = @[]
    for key, value in v.pairs:
      parts.add(py_repr_item(key) & ": " & py_repr_item(value))
    "{" & parts.join(", ") & "}"
  elif compiles($v):
    $v
  elif compiles($v[]):
    $v[]
  else:
    "<object>"

proc py_bool*(v: auto): bool =
  when v is bool:
    v
  elif v is int or v is float:
    v != 0
  elif v is string:
    v.len > 0
  else:
    not v.isNil

proc py_bool*(v: PyObj): bool =
  if v.isNil:
    false
  elif v of PyBoolObj:
    PyBoolObj(v).value
  elif v of PyIntObj:
    PyIntObj(v).value != 0
  elif v of PyFloatObj:
    PyFloatObj(v).value != 0.0
  elif v of PyStrObj:
    PyStrObj(v).value.len > 0
  else:
    true

proc py_ord*(c: string): int =
  if c.len > 0: int(c[0]) else: 0

proc py_chr*(i: int): string =
  $chr(i)

# ---------------------------------------------------------------------------
# String methods
# ---------------------------------------------------------------------------
proc py_str_strip*(s: string): string = s.strip()
proc py_str_strip*(s: string, chars: string): string =
  var charset: set[char] = {}
  for c in chars: charset.incl(c)
  s.strip(chars = charset)
proc py_str_lstrip*(s: string): string = s.strip(trailing = false)
proc py_str_lstrip*(s: string, chars: string): string =
  var charset: set[char] = {}
  for c in chars: charset.incl(c)
  s.strip(trailing = false, chars = charset)
proc py_str_rstrip*(s: string): string = s.strip(leading = false)
proc py_str_rstrip*(s: string, chars: string): string =
  var charset: set[char] = {}
  for c in chars: charset.incl(c)
  s.strip(leading = false, chars = charset)
proc py_str_startswith*(s: string, prefix: string): bool = s.startsWith(prefix)
proc py_str_startswith*(s: string, prefixes: tuple): bool =
  for p in prefixes.fields:
    if s.startsWith(p): return true
  return false
proc py_str_endswith*(s: string, suffix: string): bool = s.endsWith(suffix)
proc py_str_endswith*(s: string, suffixes: tuple): bool =
  for p in suffixes.fields:
    if s.endsWith(p): return true
  return false
proc py_str_replace*(s: string, old: string, new_str: string): string = s.replace(old, new_str)
proc py_str_find*(s: string, sub: string): int = s.find(sub)
proc py_str_rfind*(s: string, sub: string): int =
  var last = -1
  var pos = 0
  while pos < s.len:
    let found = s.find(sub, pos)
    if found < 0: break
    last = found
    pos = found + 1
  return last
# `x in (a, b, c)` membership — Python allows tuple membership test.
# Nim has no direct `contains(tuple, elem)` so provide it via fields iterator.
proc contains*(t: tuple, item: string): bool =
  for f in t.fields:
    when f is string:
      if f == item: return true
  return false

proc py_str_split*(s: string): seq[string] = s.splitWhitespace()
proc py_str_split*(s: string, sep: string): seq[string] = s.split(sep)
proc py_str_split*(s: string, sep: string, maxsplit: int): seq[string] =
  if maxsplit < 0:
    return s.split(sep)
  s.split(sep, maxsplit)
proc py_str_split*(s: string, sep: string, maxsplit: int64): seq[string] =
  py_str_split(s, sep, int(maxsplit))
proc py_str_join*(sep: string, items: seq[string]): string = items.join(sep)
proc py_str_upper*(s: string): string = s.toUpperAscii()
proc py_str_lower*(s: string): string = s.toLowerAscii()
proc py_str_count*(s: string, sub: string): int = s.count(sub)
proc py_str_index*(s: string, sub: string): int =
  let i = s.find(sub)
  if i < 0: raise newException(ValueError, "substring not found")
  return i
proc py_index*[T](s: openArray[T], idx: int): T =
  var realIdx = idx
  if realIdx < 0:
    realIdx = s.len + realIdx
  if realIdx < 0 or realIdx >= s.len:
    raise newException(IndexError, "index out of range")
  return s[realIdx]

proc py_index*[T](s: T, idx: int): auto =
  var realIdx = idx
  when compiles(s.len):
    if realIdx < 0:
      realIdx = s.len + realIdx
    if realIdx < 0 or realIdx >= s.len:
      raise newException(IndexError, "index out of range")
  return s[realIdx]
proc py_str_isdigit*(s: string): bool = s.len > 0 and s.allCharsInSet(Digits)
proc py_str_isalpha*(s: string): bool = s.len > 0 and s.allCharsInSet(Letters)
proc py_str_isalnum*(s: string): bool = s.len > 0 and s.allCharsInSet(Letters + Digits)
proc py_str_isspace*(s: string): bool = s.len > 0 and s.allCharsInSet(Whitespace)

proc py_isdigit*(v: char): bool = v.isDigit()
proc py_isdigit*(v: string): bool = v.len > 0 and v[0].isDigit()
proc py_isalpha*(v: char): bool = v.isAlphaAscii()
proc py_isalpha*(v: string): bool = v.len > 0 and v[0].isAlphaAscii()

# ---------------------------------------------------------------------------
# Builtins
# ---------------------------------------------------------------------------
proc py_len*(v: string): int = v.len
proc py_len*[T](v: seq[T]): int = v.len
proc py_len*[K, V](v: Table[K, V]): int = v.len
proc py_len*[T](v: HashSet[T]): int = v.len

proc py_repeat*(s: string, n: SomeInteger): string =
  if n <= 0:
    return ""
  result = repeat(s, int(n))

proc py_repeat*[T](items: openArray[T], n: SomeInteger): seq[T] =
  if n <= 0:
    return @[]
  result = @[]
  for _ in 0..<int(n):
    for item in items:
      result.add(item)

template py_truthy*(v: auto): bool =
  when v is bool:
    v
  elif v is SomeInteger or v is SomeFloat:
    v != 0
  elif v is string or v is seq or v is Table or v is HashSet:
    v.len > 0
  else:
    not v.isNil

proc py_round*(v: float64): int64 = int64(round(v))
proc py_round*(v: float64, ndigits: int): float64 =
  let factor = pow(10.0, float64(ndigits))
  round(v * factor) / factor

proc py_sum*[T](items: seq[T]): T =
  var total: T = T(0)
  for item in items:
    total += item
  return total

proc py_sorted*[T](items: seq[T]): seq[T] =
  var copy = items
  copy.sort()
  return copy

proc py_sorted*[T](items: HashSet[T]): seq[T] =
  var copy: seq[T] = @[]
  for item in items:
    copy.add(item)
  copy.sort()
  return copy

proc py_update*[T](dst: var HashSet[T], items: seq[T]) =
  for item in items:
    dst.incl(item)

proc py_update*[T](dst: var HashSet[T], items: HashSet[T]) =
  for item in items:
    dst.incl(item)

proc py_update*[T](dst: var HashSet[T], items: seq[PyObj]) =
  discard

proc py_reversed*[T](items: seq[T]): seq[T] =
  var copy = items
  copy.reverse()
  return copy

proc py_reversed_object*[T](items: seq[T]): seq[T] = py_reversed(items)
proc py_list_ctor*[T](items: seq[T]): seq[T] = items

proc py_enumerate*[T](items: seq[T]): seq[(int, T)] =
  var result_seq: seq[(int, T)] = @[]
  var i = 0
  for item in items:
    result_seq.add((i, item))
    i += 1
  return result_seq

proc py_enumerate*[T](items: seq[T], start: int): seq[(int, T)] =
  var result_seq: seq[(int, T)] = @[]
  var i = start
  for item in items:
    result_seq.add((i, item))
    i += 1
  return result_seq

proc py_zip*[A, B](a: seq[A], b: seq[B]): seq[(A, B)] =
  var result_seq: seq[(A, B)] = @[]
  let n = min(a.len, b.len)
  for i in 0 ..< n:
    result_seq.add((a[i], b[i]))
  return result_seq

proc py_in*[T](item: T, items: seq[T]): bool = item in items
proc py_in*(item: string, items: string): bool = item in items

# ---------------------------------------------------------------------------
# Math
# ---------------------------------------------------------------------------
proc py_floordiv*(a, b: int64): int64 =
  if b == 0: raise newException(DivByZeroDefect, "integer division by zero")
  let d = a div b
  if (a xor b) < 0 and d * b != a:
    return d - 1
  return d

proc py_mod*[T: int64 | float64](a, b: T): T =
  if b == T(0): return T(0)
  let r = a mod b
  if (r > T(0) and b < T(0)) or (r < T(0) and b > T(0)):
    r + b
  else:
    r

# ---------------------------------------------------------------------------
# Range iterator
# ---------------------------------------------------------------------------
proc py_range*(start: int, stop: int, step: int): seq[int64] =
  result = @[]
  if step != 0:
    var i = start
    if step > 0:
      while i < stop:
        result.add(int64(i))
        i += step
    else:
      while i > stop:
        result.add(int64(i))
        i += step

# ---------------------------------------------------------------------------
# Container helpers
# ---------------------------------------------------------------------------
proc pop*[T](s: var seq[T]): T =
  if s.len == 0: raise newException(IndexDefect, "pop from empty list")
  result = s[s.len - 1]
  s.setLen(s.len - 1)

proc pop*[T](s: var seq[T], idx: int): T =
  if idx < 0 or idx >= s.len: raise newException(IndexDefect, "pop index out of range")
  result = s[idx]
  s.delete(idx)

# ---------------------------------------------------------------------------
# Assertions (test framework)
# ---------------------------------------------------------------------------
proc py_assert_true*(cond: bool, msg: string = ""): bool =
  if not cond:
    if msg.len > 0:
      raise newException(AssertionDefect, msg & ": assertion failed")
    raise newException(AssertionDefect, "assertion failed")
  return true

proc py_assert_eq*[T](a, b: T, msg: string = ""): bool =
  if a != b:
    let detail = if msg != "": msg & ": " else: ""
    raise newException(AssertionDefect, detail & "assertion failed: " & $a & " != " & $b)
  return true

proc py_assert_eq*[A, B](a: seq[A], b: seq[B], msg: string = ""): bool =
  if py_to_string(a) != py_to_string(b):
    let detail = if msg != "": msg & ": " else: ""
    raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != " & py_to_string(b))
  return true

proc py_assert_eq*[T](a: PyObj, b: T, msg: string = ""): bool =
  if a.isNil:
    let detail = if msg != "": msg & ": " else: ""
    raise newException(AssertionDefect, detail & "assertion failed: None != " & $b)
  when T is string:
    if not (a of PyStrObj) or PyStrObj(a).value != b:
      let detail = if msg != "": msg & ": " else: ""
      raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != " & b)
  elif T is bool:
    if not (a of PyBoolObj) or PyBoolObj(a).value != b:
      let detail = if msg != "": msg & ": " else: ""
      raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != " & $b)
  elif T is SomeInteger:
    if not (a of PyIntObj) or PyIntObj(a).value != int64(b):
      let detail = if msg != "": msg & ": " else: ""
      raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != " & $b)
  elif T is SomeFloat:
    if not (a of PyFloatObj) or PyFloatObj(a).value != float64(b):
      let detail = if msg != "": msg & ": " else: ""
      raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != " & $b)
  else:
    let detail = if msg != "": msg & ": " else: ""
    raise newException(AssertionDefect, detail & "unsupported PyObj comparison")
  return true

proc py_assert_eq*(a: PyObj, b: typeof(nil), msg: string = ""): bool =
  if not a.isNil:
    let detail = if msg != "": msg & ": " else: ""
    raise newException(AssertionDefect, detail & "assertion failed: " & py_to_string(a) & " != None")
  return true

proc py_assert_stdout*(expected: seq[string], fn: proc()): bool =
  py_capture_stdout_active = true
  py_capture_stdout_lines = @[]
  fn()
  let captured = py_capture_stdout_lines
  py_capture_stdout_active = false
  py_capture_stdout_lines = @[]
  if captured.len != expected.len:
    return false
  var i = 0
  while i < captured.len:
    if captured[i] != expected[i]:
      return false
    i += 1
  return true

proc py_assert_all*(items: seq[bool], msg: string = ""): bool =
  for item in items:
    if not item:
      let detail = if msg != "": msg & ": " else: ""
      raise newException(AssertionDefect, detail & "assert_all failed")
  return true

# ---------------------------------------------------------------------------
# Format helper
# ---------------------------------------------------------------------------
proc py_insert_commas(s: string): string =
  var sign = ""
  var digits = s
  if digits.len > 0 and (digits[0] == '-' or digits[0] == '+'):
    sign = $digits[0]
    digits = digits[1 .. ^1]
  var parts: seq[string] = @[]
  var i = digits.len
  while i > 3:
    parts.insert(digits[i - 3 ..< i], 0)
    i -= 3
  if i > 0:
    parts.insert(digits[0 ..< i], 0)
  return sign & parts.join(",")

proc py_pad_text(s: string, width: int, left_align: bool = false, fill: char = ' '): string =
  if s.len >= width:
    return s
  let pad = repeat($fill, width - s.len)
  if left_align:
    return s & pad
  return pad & s

proc py_fmt*(v: string, spec: string): string =
  var text = v
  if spec.len == 0:
    return text
  let kind = spec[^1]
  var body = if kind in {'s'}: spec[0 ..< spec.len - 1] else: spec
  var left_align = false
  if body.startsWith("<"):
    left_align = true
    body = body[1 .. ^1]
  if body.len > 0:
    let width = parseInt(body)
    return py_pad_text(text, width, left_align = left_align)
  return text

proc py_fmt*(v: SomeInteger, spec: string): string =
  if spec.len == 0:
    return $v
  let kind = spec[^1]
  var body = spec[0 ..< spec.len - 1]
  var show_sign = false
  var zero_fill = false
  var comma_group = false
  if body.startsWith("+"):
    show_sign = true
    body = body[1 .. ^1]
  if body.startsWith("0"):
    zero_fill = true
  if body.contains(","):
    comma_group = true
    body = body.replace(",", "")
  let width = if body.len > 0: parseInt(body) else: 0
  var text = ""
  if kind == 'x' or kind == 'X':
    text = toHex(uint64(v))
    while text.len > 1 and text[0] == '0':
      text = text[1 .. ^1]
    if kind == 'x':
      text = text.toLowerAscii()
  else:
    text = $v
    if comma_group:
      text = py_insert_commas(text)
  if show_sign and v >= 0:
    text = "+" & text
  if width > 0:
    let fill = if zero_fill and not comma_group: '0' else: ' '
    if fill == '0' and text.len > 0 and (text[0] == '+' or text[0] == '-'):
      let sign = text[0]
      text = $sign & py_pad_text(text[1 .. ^1], width - 1, fill = fill)
    else:
      text = py_pad_text(text, width, fill = fill)
  return text

proc py_fmt*(v: SomeFloat, spec: string): string =
  if spec.len == 0:
    return $v
  let kind = spec[^1]
  var body = spec[0 ..< spec.len - 1]
  var width = 0
  var prec = -1
  if "." in body:
    let parts = body.split(".")
    if parts[0].len > 0:
      width = parseInt(parts[0])
    if parts.len > 1 and parts[1].len > 0:
      prec = parseInt(parts[1])
  elif body.len > 0:
    width = parseInt(body)
  if prec < 0:
    prec = 6
  var value = float64(v)
  var suffix = ""
  if kind == '%':
    value *= 100.0
    suffix = "%"
  let text = formatFloat(value, ffDecimal, prec) & suffix
  if width > 0:
    return py_pad_text(text, width)
  return text

proc py_fmt*(v: auto, spec: string): string =
  py_to_string(v)

# ---------------------------------------------------------------------------
# Binary file I/O helpers
# ---------------------------------------------------------------------------
proc py_write_bytes*(f: File, data: seq[uint8]) =
  if data.len > 0:
    discard f.writeBuffer(unsafeAddr data[0], data.len)

proc py_write_bytes*(f: File, data: seq[int]) =
  if data.len > 0:
    var buf = newSeq[uint8](data.len)
    for i in 0 ..< data.len:
      buf[i] = uint8(data[i] and 0xFF)
    discard f.writeBuffer(unsafeAddr buf[0], buf.len)

# Image functions (write_rgb_png, save_gif, grayscale_palette) are provided
# by emitter-generated utils/png.nim and utils/gif.nim modules (§6).
