include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc fire_palette*(): auto =
  var p = newSeq[uint8]()
  for i in 0 ..< 256:
    var r = 0
    var g = 0
    var b = 0
    if (i < 85):
      r = (i * 3)
      g = 0
      b = 0
    elif (i < 170):
      r = 255
      g = ((i - 85) * 3)
      b = 0
    else:
      r = 255
      g = 255
      b = ((i - 170) * 3)
    p.add(uint8(r))
    p.add(uint8(g))
    p.add(uint8(b))
  return bytes(p)

proc run_09_fire_simulation*(): auto =
  var w = 380
  var h = 260
  var steps = 420
  var out_path = "sample/out/09_fire_simulation.gif"
  var start = epochTime()
  var heat: seq[seq[int]] = (block: var res: seq[auto] = @[]; for v in /* unknown expr RangeExpr */: res.add((@[0] * w)); res)
  var frames: seq[auto] = @[]
  for t in 0 ..< steps:
    for x in 0 ..< w:
      var val = (170 + py_mod(((x * 13) + (t * 17)), 86))
      heat[(h - 1)][x] = val
    for y in 1 ..< h:
      for x in 0 ..< w:
        var a = heat[y][x]
        var b = heat[y][py_mod(((x - 1) + w), w)]
        var c = heat[y][py_mod((x + 1), w)]
        var d = heat[py_mod((y + 1), h)][x]
        var v = ((((a + b) + c) + d) div 4)
        var cool = (1 + py_mod(((x + y) + t), 3))
        var nv = (v - cool)
        heat[(y - 1)][x] = /* unknown expr IfExp */
    var frame = newSeq[uint8]()
    for yy in 0 ..< h:
      var row_base = (yy * w)
      for xx in 0 ..< w:
        frame[(row_base + xx)] = heat[yy][xx]
    frames.add(bytes(frame))
  discard save_gif(out_path, w, h, frames, fire_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", steps
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_09_fire_simulation()
