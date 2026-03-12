# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/iter_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for object-based iterator helpers."
proc py_reversed_object*(values: auto): seq[auto] =
  var `out`: seq[auto] = @[]
  var i: int = 0
  `out` = @[] # seq[auto]
  i = (values.len - 1)
  while (i >= 0):
    `out`.add(values[i])
    i -= 1
  return `out`

proc py_enumerate_object*(values: auto, start: int): seq[auto] =
  var `out`: seq[auto] = @[]
  var i: int = 0
  var n: int = 0
  `out` = @[] # seq[auto]
  i = 0
  n = values.len
  while (i < n):
    `out`.add(@[(start + i), values[i]])
    i += 1
  return `out`
