include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc palette*(): auto =
  var p = newSeq[uint8]()
  for i in 0 ..< 256:
    var r = min(255, int((20 + (i * 0.9))))
    var g = min(255, int((10 + (i * 0.7))))
    var b = min(255, (30 + i))
    p.add(uint8(r))
    p.add(uint8(g))
    p.add(uint8(b))
  return bytes(p)

proc scene*(x: float, y: float, light_x: float, light_y: float): auto =
  var x1 = (x + 0.45)
  var y1 = (y + 0.2)
  var x2 = (x - 0.35)
  var y2 = (y - 0.15)
  var r1 = sqrt(((x1 * x1) + (y1 * y1)))
  var r2 = sqrt(((x2 * x2) + (y2 * y2)))
  var blob = (math.exp((((-7.0) * r1) * r1)) + math.exp((((-8.0) * r2) * r2)))
  var lx = (x - light_x)
  var ly = (y - light_y)
  var l = sqrt(((lx * lx) + (ly * ly)))
  var lit = (float(1.0) / float((1.0 + ((3.5 * l) * l))))
  var v = int((((255.0 * blob) * lit) * 5.0))
  return min(255, max(0, v))

proc run_14_raymarching_light_cycle*(): auto =
  var w = 320
  var h = 240
  var frames_n = 84
  var out_path = "sample/out/14_raymarching_light_cycle.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  var v_hoisted_cast_1: float = float(frames_n)
  var v_hoisted_cast_2: float = float((h - 1))
  var v_hoisted_cast_3: float = float((w - 1))
  for t in 0 ..< frames_n:
    var frame = newSeq[uint8]()
    var a = (((float(t) / float(v_hoisted_cast_1)) * math.pi) * 2.0)
    var light_x = (0.75 * math.cos(a))
    var light_y = (0.55 * math.sin((a * 1.2)))
    for y in 0 ..< h:
      var row_base = (y * w)
      var py = (((float(y) / float(v_hoisted_cast_2)) * 2.0) - 1.0)
      for x in 0 ..< w:
        var px = (((float(x) / float(v_hoisted_cast_3)) * 2.0) - 1.0)
        frame[(row_base + x)] = scene(px, py, light_x, light_y)
    frames.add(bytes(frame))
  discard save_gif(out_path, w, h, frames, palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames_n
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_14_raymarching_light_cycle()
