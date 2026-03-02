include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc render*(values: seq[int], w: int, h: int): auto =
  var frame = newSeq[uint8]()
  var n = values.len
  var bar_w = (float(w) / float(n))
  var v_hoisted_cast_1: float = float(n)
  var v_hoisted_cast_2: float = float(h)
  for i in 0 ..< n:
    var x0 = int((i * bar_w))
    var x1 = int(((i + 1) * bar_w))
    if (x1 <= x0):
      x1 = (x0 + 1)
    var bh = int(((float(values[i]) / float(v_hoisted_cast_1)) * v_hoisted_cast_2))
    var y = (h - bh)
    for y in y ..< h:
      for x in x0 ..< x1:
        frame[((y * w) + x)] = 255
  return bytes(frame)

proc run_12_sort_visualizer*(): auto =
  var w = 320
  var h = 180
  var n = 124
  var out_path = "sample/out/12_sort_visualizer.gif"
  var start = epochTime()
  var values: seq[int] = @[]
  for i in 0 ..< n:
    values.add(py_mod(((i * 37) + 19), n))
  var frames: seq[auto] = @[render(values, w, h)]
  var frame_stride = 16
  var op = 0
  for i in 0 ..< n:
    var swapped = false
    for j in 0 ..< ((n - i) - 1):
      if (values[j] > values[(j + 1)]):
        (values[j], values[(j + 1)]) = (values[(j + 1)], values[j])
        swapped = true
      if (py_mod(op, frame_stride) == 0):
        frames.add(render(values, w, h))
      op += 1
    if py_truthy((not py_truthy(swapped))):
      discard `break`
  discard save_gif(out_path, w, h, frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames.len
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_12_sort_visualizer()
