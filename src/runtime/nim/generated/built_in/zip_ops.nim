# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/zip_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for generic zip helpers."
proc zip*(lhs: seq[auto], rhs: seq[auto]): seq[(auto, auto)] =
  var `out`: seq[(auto, auto)] = @[]
  var i: int = 0
  var n: int = 0
  `out` = @[] # seq[(auto, auto)]
  i = 0
  n = lhs.len
  if (rhs.len < n):
    n = rhs.len
  while (i < n):
    `out`.add((lhs[i], rhs[i]))
    i += 1
  return `out`
