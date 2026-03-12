# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/predicates.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for predicate helpers."
proc py_any*(values: auto): bool =
  var i: int = 0
  var n: int = 0
  i = 0
  n = values.len
  while (i < n):
    if py_truthy(py_truthy(values[i])):
      return true
    i += 1
  return false

proc py_all*(values: auto): bool =
  var i: int = 0
  var n: int = 0
  i = 0
  n = values.len
  while (i < n):
    if py_truthy((not py_truthy(py_truthy(values[i])))):
      return false
    i += 1
  return true
