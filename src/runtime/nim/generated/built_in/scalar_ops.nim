# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/scalar_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Extern-marked scalar helper built-ins."
proc py_to_int64_base*(v: string, base: int): auto =
  return v_b.int(v, base)

proc py_ord*(ch: string): auto =
  return v_b.ord(ch)

proc py_chr*(codepoint: int): auto =
  return v_b.chr(codepoint)
