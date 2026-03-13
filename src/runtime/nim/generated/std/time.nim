# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/time.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.time: extern-marked time API with Python runtime fallback."
proc perf_counter*(): auto =
  return v_t.perf_counter()
