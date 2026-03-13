# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/math.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.math: extern-marked math API with Python runtime fallback."
var pi: float = extern(PI)
var e: float = extern(E)
proc sqrt*(x: float): float =
  return math.sqrt(float(x))

proc sin*(x: float): float =
  return v_m.sin(x)

proc cos*(x: float): float =
  return v_m.cos(x)

proc tan*(x: float): float =
  return v_m.tan(x)

proc exp*(x: float): float =
  return v_m.exp(x)

proc log*(x: float): float =
  return v_m.log(x)

proc log10*(x: float): float =
  return v_m.log10(x)

proc fabs*(x: float): float =
  return v_m.fabs(x)

proc floor*(x: float): float =
  return v_m.floor(x)

proc ceil*(x: float): float =
  return v_m.ceil(x)

proc pow*(x: float, y: float): float =
  return v_m.pow(x, y)
