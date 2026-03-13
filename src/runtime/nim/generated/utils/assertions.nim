# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/utils/assertions.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

proc veq_any*(actual: auto, expected: auto): bool =
  return (py_to_string(actual) == py_to_string(expected))
  return (actual == expected)

proc py_assert_true*(cond: bool, label: string): bool =
  if py_truthy(cond):
    return true
  if (label != ""):
    echo py_str(0)
  else:
    echo py_str("[assert_true] False")
  return false

proc py_assert_eq*(actual: auto, expected: auto, label: string): bool =
  var ok: bool = false
  ok = veq_any(actual, expected)
  if py_truthy(ok):
    return true
  if (label != ""):
    echo py_str(0)
  else:
    echo py_str(0)
  return false

proc py_assert_all*(results: seq[bool], label: string): bool =
  for v in results:
    if py_truthy((not py_truthy(v))):
      if (label != ""):
        echo py_str(0)
      else:
        echo py_str("[assert_all] False")
      return false
  return true

proc py_assert_stdout*(expected_lines: seq[string], fn: auto): bool =
  return true
