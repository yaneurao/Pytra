include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc run_integer_grid_checksum*(width: int, height: int, seed: int): auto =
  var mod_main: int = 2147483647
  var mod_out: int = 1000000007
  var acc: int = py_mod(seed, mod_out)
  for y in 0 ..< height:
    var row_sum: int = 0
    for x in 0 ..< width:
      var v: int = py_mod((((x * 37) + (y * 73)) + seed), mod_main)
      v = py_mod(((v * 48271) + 1), mod_main)
      row_sum += py_mod(v, 256)
    acc = py_mod((acc + (row_sum * (y + 1))), mod_out)
  return acc

proc run_integer_benchmark*(): auto =
  var width: int = 7600
  var height: int = 5000
  var start: float = epochTime()
  var checksum: int = run_integer_grid_checksum(width, height, 123456789)
  var elapsed: float = (epochTime() - start)
  echo "pixels:", (width * height)
  echo "checksum:", checksum
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_integer_benchmark()
