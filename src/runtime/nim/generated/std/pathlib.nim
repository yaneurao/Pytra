# AUTO-GENERATED FILE. DO NOT EDIT.
# source: src/pytra/std/pathlib.py
# generated-by: tools/gen_runtime_from_manifest.py

include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math, std/sequtils

discard "Pure Python Path helper compatible with a subset of pathlib.Path."
type Path* = ref object
  vvalue*: string

proc v_str__*(self: Path): string
proc v_repr__*(self: Path): string
proc v_fspath__*(self: Path): string
proc v_truediv__*(self: Path, rhs: string): Path
proc parent*(self: Path): Path
proc parents*(self: Path): seq[Path]
proc name*(self: Path)
proc suffix*(self: Path)
proc stem*(self: Path)
proc resolve*(self: Path): Path
proc exists*(self: Path)
proc mkdir*(self: Path, parents: bool, exist_ok: bool)
proc read_text*(self: Path, encoding: string)
proc write_text*(self: Path, text: string, encoding: string)
proc glob*(self: Path, pattern: string): seq[Path]
proc cwd*(): Path

proc newPath*(value: string): Path =
  new(result)
  result.vvalue = value

proc v_str__*(self: Path): string =
  return self.vvalue

proc v_repr__*(self: Path): string =
  return ($(($("Path(") & $(self.vvalue))) & $(")"))

proc v_fspath__*(self: Path): string =
  return self.vvalue

proc v_truediv__*(self: Path, rhs: string): Path =
  return newPath(path.join(self.vvalue, rhs))

proc parent*(self: Path): Path =
  var parent_txt: string = ""
  parent_txt = path.dirname(self.vvalue)
  if (parent_txt == ""):
    parent_txt = "."
  return newPath(parent_txt)

proc parents*(self: Path): seq[Path] =
  var `out`: seq[Path] = @[]
  var current: string = ""
  var next_current: string = ""
  `out` = @[] # seq[Path]
  current = path.dirname(self.vvalue) # string
  while true:
    if (current == ""):
      current = "."
    `out`.add(newPath(current))
    next_current = path.dirname(current)
    if (next_current == ""):
      next_current = "."
    if (next_current == current):
      break
    current = next_current
  return `out`

proc name*(self: Path): auto =
  return path.basename(self.vvalue)

proc suffix*(self: Path): auto =
  var (v, ext) = path.splitext(path.basename(self.vvalue))
  return ext

proc stem*(self: Path): auto =
  var (root, v) = path.splitext(path.basename(self.vvalue))
  return root

proc resolve*(self: Path): Path =
  return newPath(path.abspath(self.vvalue))

proc exists*(self: Path): auto =
  return path.exists(self.vvalue)

proc mkdir*(self: Path, parents: bool, exist_ok: bool) =
  if py_truthy(parents):
    os.makedirs(self.vvalue, exist_ok)
    return 
  if py_truthy((py_truthy(exist_ok) and py_truthy(path.exists(self.vvalue)))):
    return 
  os.mkdir(self.vvalue)

proc read_text*(self: Path, encoding: string): auto =
  var f = open(self.vvalue, "r", encoding)
  return f.read()
  f.close()

proc write_text*(self: Path, text: string, encoding: string) =
  var f = open(self.vvalue, "w", encoding)
  return f.write(text)
  f.close()

proc glob*(self: Path, pattern: string): seq[Path] =
  var `out`: seq[Path] = @[]
  var paths: seq[string] = @[]
  paths = py_glob.glob(path.join(self.vvalue, pattern)) # seq[string]
  `out` = @[] # seq[Path]
  for p in paths:
    `out`.add(newPath(p))
  return `out`

proc cwd*(): Path =
  return newPath(os.getcwd())
