# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/sys.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "pytra.std.sys: extern-marked sys API with Python runtime fallback."
var argv: seq[string] = extern(v_s.argv)
var path: seq[string] = extern(v_s.path)
var stderr = extern(v_s.stderr)
var stdout = extern(v_s.stdout)
proc exit*(code: int) =
  v_s.exit(code)

proc set_argv*(values: seq[string]) =
  argv.clear()
  for v in values:
    argv.add(v)

proc set_path*(values: seq[string]) =
  path.clear()
  for v in values:
    path.add(v)

proc write_stderr*(text: string) =
  v_s.stderr.write(text)

proc write_stdout*(text: string) =
  v_s.stdout.write(text)
