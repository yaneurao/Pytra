# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/os_path.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.os_path: extern-marked os.path subset with Python runtime fallback."
proc join*(a: string, b: string): auto =
  return v_path.join(a, b)

proc dirname*(p: string): auto =
  return v_path.dirname(p)

proc basename*(p: string): auto =
  return v_path.basename(p)

proc splitext*(p: string): auto =
  return v_path.splitext(p)

proc abspath*(p: string): auto =
  return v_path.abspath(p)

proc exists*(p: string): auto =
  return v_path.exists(p)
