include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc color_palette*(): auto =
  var p = newSeq[uint8]()
  for i in 0 ..< 256:
    var r = i
    var g = py_mod((i * 3), 256)
    var b = (255 - i)
    p.add(uint8(r))
    p.add(uint8(g))
    p.add(uint8(b))
  return bytes(p)

proc run_11_lissajous_particles*(): auto =
  var w = 320
  var h = 240
  var frames_n = 360
  var particles = 48
  var out_path = "sample/out/11_lissajous_particles.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  for t in 0 ..< frames_n:
    var frame = newSeq[uint8]()
    var v_hoisted_cast_1: float = float(t)
    for p in 0 ..< particles:
      var phase = (p * 0.261799)
      var x = int(((w * 0.5) + ((w * 0.38) * math.sin(((0.11 * v_hoisted_cast_1) + (phase * 2.0))))))
      var y = int(((h * 0.5) + ((h * 0.38) * math.sin(((0.17 * v_hoisted_cast_1) + (phase * 3.0))))))
      var color = (30 + py_mod((p * 9), 220))
      for dy in (-2) ..< 3:
        for dx in (-2) ..< 3:
          var xx = (x + dx)
          var yy = (y + dy)
          if py_truthy(((xx >= 0) {op} (xx < w) {op} (yy >= 0) {op} (yy < h))):
            var d2 = ((dx * dx) + (dy * dy))
            if (d2 <= 4):
              var idx = ((yy * w) + xx)
              var v = (color - (d2 * 20))
              v = /* unknown expr Unbox */
              if (v > frame[idx]):
                frame[idx] = /* unknown expr Unbox */
    frames.add(bytes(frame))
  discard save_gif(out_path, w, h, frames, color_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames_n
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_11_lissajous_particles()
