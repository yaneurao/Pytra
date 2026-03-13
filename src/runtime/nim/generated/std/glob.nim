# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/glob.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.glob: extern-marked glob subset with Python runtime fallback."
proc glob*(pattern: string): auto =
  return v_glob.glob(pattern)
