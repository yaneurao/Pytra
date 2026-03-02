include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc capture*(grid: seq[seq[int]], w: int, h: int): auto =
  var frame = newSeq[uint8]()
  for y in 0 ..< h:
    var row_base = (y * w)
    for x in 0 ..< w:
      frame[(row_base + x)] = /* unknown expr IfExp */
  return bytes(frame)

proc run_08_langtons_ant*(): auto =
  var w = 420
  var h = 420
  var out_path = "sample/out/08_langtons_ant.gif"
  var start = epochTime()
  var grid: seq[seq[int]] = (block: var res: seq[auto] = @[]; for v in /* unknown expr RangeExpr */: res.add((@[0] * w)); res)
  var x = (w div 2)
  var y = (h div 2)
  var d = 0
  var steps_total = 600000
  var capture_every = 3000
  var frames: seq[auto] = @[]
  for i in 0 ..< steps_total:
    if (grid[y][x] == 0):
      d = py_mod((d + 1), 4)
      grid[y][x] = 1
    else:
      d = py_mod((d + 3), 4)
      grid[y][x] = 0
    if (d == 0):
      y = py_mod(((y - 1) + h), h)
    elif (d == 1):
      x = py_mod((x + 1), w)
    elif (d == 2):
      y = py_mod((y + 1), h)
    else:
      x = py_mod(((x - 1) + w), w)
    if (py_mod(i, capture_every) == 0):
      frames.add(capture(grid, w, h))
  discard save_gif(out_path, w, h, frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames.len
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_08_langtons_ant()
