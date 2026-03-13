# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/built_in/io_ops.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Extern-marked I/O helper built-ins."
proc py_print*(value: auto) =
  v_b.print(value)
