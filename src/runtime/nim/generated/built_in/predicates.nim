# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/predicates.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure-Python source-of-truth for predicate helpers."
proc py_any*(values: auto): bool =
  for value in values:
    if py_truthy(py_truthy(value)):
      return true
  return false

proc py_all*(values: auto): bool =
  for value in values:
    if py_truthy((not py_truthy(py_truthy(value)))):
      return false
  return true
