# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/timeit.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.timeit compatibility shim."
proc default_timer*(): float =
  return epochTime()
