# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/sequence.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for sequence helpers used by runtime built-ins."
proc py_range*(start: int, stop: int, step: int): seq[int] =
  var `out`: seq[int] = @[]
  var i: int = 0
  `out` = @[] # seq[int]
  if (step == 0):
    return `out`
  if (step > 0):
    i = start
    while (i < stop):
      `out`.add(i)
      i += step
  else:
    i = start
    while (i > stop):
      `out`.add(i)
      i += step
  return `out`

proc py_repeat*(v: string, n: int): string =
  var `out`: string = ""
  var i: int = 0
  if (n <= 0):
    return ""
  `out` = ""
  i = 0
  while (i < n):
    `out` += v
    i += 1
  return `out`
