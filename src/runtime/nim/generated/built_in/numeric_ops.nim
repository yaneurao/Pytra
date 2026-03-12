# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/numeric_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for numeric helper built-ins."
proc sum*(values: seq[auto]): int =
  var i: int = 0
  var n: int = 0
  if (values.len == 0):
    return 0
  var acc = (values[0] - values[0])
  i = 0
  n = values.len
  while (i < n):
    acc += values[i]
    i += 1
  return acc

proc py_min*(a: auto, b: auto): auto =
  if (a < b):
    return a
  return b

proc py_max*(a: auto, b: auto): auto =
  if (a > b):
    return a
  return b
