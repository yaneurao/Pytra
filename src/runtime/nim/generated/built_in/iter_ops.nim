# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/iter_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for object-based iterator helpers."
proc py_reversed_object*(values: auto): auto =
  var `out`: seq[auto] = @[]
  `out` = @[] # seq[auto]
  for value in values:
    `out`.add(value)
  return reversed(`out`)

proc py_enumerate_object*(values: auto, start: int): seq[auto] =
  var `out`: seq[auto] = @[]
  var i: int = 0
  `out` = @[] # seq[auto]
  i = start
  for value in values:
    `out`.add(@[i, value])
    i += 1
  return `out`
