# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/os.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.os: extern-marked os subset with Python runtime fallback."
proc getcwd*(): auto =
  return v_os.getcwd()

proc mkdir*(p: string) =
  v_os.mkdir(p)

proc makedirs*(p: string, exist_ok: bool) =
  v_os.makedirs(p, exist_ok)
