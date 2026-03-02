# Nim runtime for Pytra
import std/os
import std/times
import std/tables
import std/strutils
import std/math

proc py_perf_counter*(): float =
  epochTime()

# Pytra built-ins
proc py_int*(v: auto): int =
  when v is string:
    parseInt(v)
  else:
    int(v)

proc py_float*(v: auto): float =
  when v is string:
    parseFloat(v)
  else:
    float(v)

proc py_str*(v: auto): string =
  $v

proc py_len*(v: seq or string or Table): int =
  v.len

template py_truthy*(v: auto): bool =
  when v is bool:
    v
  elif v is int or v is float:
    v != 0
  elif v is string or v is seq or v is Table:
    v.len > 0
  else:
    not v.isNil

# Python-style modulo
proc py_mod*[T: int or float](a, b: T): T =
  if b == 0:
    return 0
  let r = a mod b
  if (r > 0 and b < 0) or (r < 0 and b > 0):
    r + b
  else:
    r

# runtime helper stubs
proc write_rgb_png*(path: string, width: int, height: int, pixels: seq[uint8]) =
  discard path
  discard width
  discard height
  discard pixels
