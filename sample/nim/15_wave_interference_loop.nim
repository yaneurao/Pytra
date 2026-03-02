include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc run_15_wave_interference_loop*(): auto =
  var w = 320
  var h = 240
  var frames_n = 96
  var out_path = "sample/out/15_wave_interference_loop.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  for t in 0 ..< frames_n:
    var frame = newSeq[uint8]()
    var phase = (t * 0.12)
    for y in 0 ..< h:
      var row_base = (y * w)
      for x in 0 ..< w:
        var dx = (x - 160)
        var dy = (y - 120)
        var v = (((math.sin(((x + (t * 1.5)) * 0.045)) + math.sin(((y - (t * 1.2)) * 0.04))) + math.sin((((x + y) * 0.02) + phase))) + math.sin(((sqrt(((dx * dx) + (dy * dy))) * 0.08) - (phase * 1.3))))
        var c = int(((v + 4.0) * (float(255.0) / float(8.0))))
        if (c < 0):
          c = 0
        if (c > 255):
          c = 255
        frame[(row_base + x)] = c
    frames.add(bytes(frame))
  discard save_gif(out_path, w, h, frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames_n
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_15_wave_interference_loop()
