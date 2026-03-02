# Nim runtime for Pytra
import std/os
import std/times
import std/tables
import std/strutils

proc py_perf_counter*(): float =
  epochTime()

# Pytra built-ins
proc py_int*(v: any): int =
  when v is string:
    parseInt(v)
  else:
    int(v)

proc py_float*(v: any): float =
  when v is string:
    parseFloat(v)
  else:
    float(v)

proc py_str*(v: any): string =
  $v

proc py_len*(v: seq or string or Table): int =
  v.len

template `py_truthy`*(v: any): bool =
  when v is bool:
    v
  elif v is int or v is float:
    v != 0
  elif v is string or v is seq or v is Table:
    v.len > 0
  else:
    v != nil
