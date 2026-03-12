# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/contains.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for containment helpers."
proc py_contains_dict_object*(values: auto, key: auto): bool =
  var needle: string = ""
  needle = $(key)
  for cur in values:
    if (cur == needle):
      return true
  return false

proc py_contains_list_object*(values: auto, key: auto): bool =
  for cur in values:
    if (cur == key):
      return true
  return false

proc py_contains_set_object*(values: auto, key: auto): bool =
  for cur in values:
    if (cur == key):
      return true
  return false

proc py_contains_str_object*(values: auto, key: auto): bool =
  var haystack: string = ""
  var i: int = 0
  var j: int = 0
  var last: int = 0
  var m: int = 0
  var n: int = 0
  var needle: string = ""
  var ok: bool = false
  needle = $(key)
  haystack = $(values)
  n = haystack.len
  m = needle.len
  if (m == 0):
    return true
  i = 0
  last = (n - m)
  while (i <= last):
    j = 0
    ok = true
    while (j < m):
      if ($(haystack[(i + j)]) != $(needle[j])):
        ok = false
        break
      j += 1
    if py_truthy(ok):
      return true
    i += 1
  return false
