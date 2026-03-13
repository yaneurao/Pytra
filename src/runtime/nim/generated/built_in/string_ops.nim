# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/string_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for string helper built-ins."
proc vis_space*(ch: string): bool =
  return ((ch == " ") or (ch == "	") or (ch == "\n") or (ch == ""))

proc vcontains_char*(chars: string, ch: string): bool =
  var i: int = 0
  var n: int = 0
  i = 0
  n = chars.len
  while (i < n):
    if ($(chars[i]) == ch):
      return true
    i += 1
  return false

proc vnormalize_index*(idx: int, n: int): int =
  var `out`: int = 0
  `out` = idx
  if (`out` < 0):
    `out` += n
  if (`out` < 0):
    `out` = 0
  if (`out` > n):
    `out` = n
  return `out`

proc py_join*(sep: string, parts: seq[string]): string =
  var `out`: string = ""
  var i: int = 0
  var n: int = 0
  n = parts.len
  if (n == 0):
    return ""
  `out` = ""
  i = 0
  while (i < n):
    if (i > 0):
      `out` += sep
    `out` += $(parts[i])
    i += 1
  return `out`

proc py_split*(s: string, sep: string, maxsplit: int): seq[string] =
  var `out`: seq[string] = @[]
  var at: int = 0
  var m: int = 0
  var n: int = 0
  var pos: int = 0
  var splits: int = 0
  var unlimited: bool = false
  `out` = @[] # seq[string]
  if (sep == ""):
    `out`.add(s)
    return `out`
  pos = 0
  splits = 0
  n = s.len
  m = sep.len
  unlimited = (maxsplit < 0)
  while true:
    if py_truthy((py_truthy((not py_truthy(unlimited))) and (splits >= maxsplit))):
      break
    at = py_find_window(s, sep, pos, n)
    if (at < 0):
      break
    `out`.add(s[pos ..< at])
    pos = (at + m)
    splits += 1
  `out`.add(s[pos ..< n])
  return `out`

proc py_splitlines*(s: string): seq[string] =
  var `out`: seq[string] = @[]
  var ch: string = ""
  var i: int = 0
  var last: string = ""
  var n: int = 0
  var start: int = 0
  `out` = @[] # seq[string]
  n = s.len
  start = 0
  i = 0
  while (i < n):
    ch = $(s[i])
    if py_truthy(((ch == "\n") or (ch == ""))):
      `out`.add(s[start ..< i])
      if py_truthy(((ch == "") and ((i + 1) < n) and ($(s[(i + 1)]) == "\n"))):
        i += 1
      i += 1
      start = i
      continue
    i += 1
  if (start < n):
    `out`.add(s[start ..< n])
  elif (n > 0):
    last = $(s[(n - 1)])
    if py_truthy(((last == "\n") or (last == ""))):
      `out`.add("")
  return `out`

proc py_count*(s: string, needle: string): int =
  var `out`: int = 0
  var at: int = 0
  var m: int = 0
  var n: int = 0
  var pos: int = 0
  if (needle == ""):
    return (s.len + 1)
  `out` = 0
  pos = 0
  n = s.len
  m = needle.len
  while true:
    at = py_find_window(s, needle, pos, n)
    if (at < 0):
      return `out`
    `out` += 1
    pos = (at + m)

proc py_lstrip*(s: string): string =
  var i: int = 0
  var n: int = 0
  i = 0
  n = s.len
  while py_truthy(((i < n) and py_truthy(vis_space($(s[i]))))):
    i += 1
  return s[i ..< n]

proc py_lstrip_chars*(s: string, chars: string): string =
  var i: int = 0
  var n: int = 0
  i = 0
  n = s.len
  while py_truthy(((i < n) and py_truthy(vcontains_char(chars, $(s[i]))))):
    i += 1
  return s[i ..< n]

proc py_rstrip*(s: string): string =
  var i: int = 0
  var n: int = 0
  n = s.len
  i = (n - 1)
  while py_truthy(((i >= 0) and py_truthy(vis_space($(s[i]))))):
    i -= 1
  return s[0 ..< (i + 1)]

proc py_rstrip_chars*(s: string, chars: string): string =
  var i: int = 0
  var n: int = 0
  n = s.len
  i = (n - 1)
  while py_truthy(((i >= 0) and py_truthy(vcontains_char(chars, $(s[i]))))):
    i -= 1
  return s[0 ..< (i + 1)]

proc py_strip*(s: string): string =
  return py_rstrip(py_lstrip(s))

proc py_strip_chars*(s: string, chars: string): string =
  return py_rstrip_chars(py_lstrip_chars(s, chars), chars)

proc py_startswith*(s: string, prefix: string): bool =
  var i: int = 0
  var m: int = 0
  var n: int = 0
  n = s.len
  m = prefix.len
  if (m > n):
    return false
  i = 0
  while (i < m):
    if ($(s[i]) != $(prefix[i])):
      return false
    i += 1
  return true

proc py_endswith*(s: string, suffix: string): bool =
  var base: int = 0
  var i: int = 0
  var m: int = 0
  var n: int = 0
  n = s.len
  m = suffix.len
  if (m > n):
    return false
  i = 0
  base = (n - m)
  while (i < m):
    if ($(s[(base + i)]) != $(suffix[i])):
      return false
    i += 1
  return true

proc py_find*(s: string, needle: string): int =
  return py_find_window(s, needle, 0, s.len)

proc py_find_window*(s: string, needle: string, start: int, `end`: int): int =
  var i: int = 0
  var j: int = 0
  var last: int = 0
  var lo: int = 0
  var m: int = 0
  var n: int = 0
  var ok: bool = false
  var up: int = 0
  n = s.len
  m = needle.len
  lo = vnormalize_index(start, n)
  up = vnormalize_index(`end`, n)
  if (up < lo):
    return (-1)
  if (m == 0):
    return lo
  i = lo
  last = (up - m)
  while (i <= last):
    j = 0
    ok = true
    while (j < m):
      if ($(s[(i + j)]) != $(needle[j])):
        ok = false
        break
      j += 1
    if py_truthy(ok):
      return i
    i += 1
  return (-1)

proc py_rfind*(s: string, needle: string): int =
  return py_rfind_window(s, needle, 0, s.len)

proc py_rfind_window*(s: string, needle: string, start: int, `end`: int): int =
  var i: int = 0
  var j: int = 0
  var lo: int = 0
  var m: int = 0
  var n: int = 0
  var ok: bool = false
  var up: int = 0
  n = s.len
  m = needle.len
  lo = vnormalize_index(start, n)
  up = vnormalize_index(`end`, n)
  if (up < lo):
    return (-1)
  if (m == 0):
    return up
  i = (up - m)
  while (i >= lo):
    j = 0
    ok = true
    while (j < m):
      if ($(s[(i + j)]) != $(needle[j])):
        ok = false
        break
      j += 1
    if py_truthy(ok):
      return i
    i -= 1
  return (-1)

proc py_replace*(s: string, oldv: string, newv: string): string =
  var `out`: string = ""
  var i: int = 0
  var m: int = 0
  var n: int = 0
  if (oldv == ""):
    return s
  `out` = ""
  n = s.len
  m = oldv.len
  i = 0
  while (i < n):
    if py_truthy((((i + m) <= n) and (py_find_window(s, oldv, i, (i + m)) == i))):
      `out` += newv
      i += m
    else:
      `out` += $(s[i])
      i += 1
  return `out`
