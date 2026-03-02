include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc render_frame*(width: int, height: int, center_x: float, center_y: float, scale: float, max_iter: int): auto =
  var frame = newSeq[uint8]()
  var v_hoisted_cast_1: float = float(max_iter)
  for y in 0 ..< height:
    var row_base = (y * width)
    var cy = (center_y + ((y - (height * 0.5)) * scale))
    for x in 0 ..< width:
      var cx = (center_x + ((x - (width * 0.5)) * scale))
      var zx = 0.0
      var zy = 0.0
      var i = 0
      while (i < max_iter):
        var zx2 = (zx * zx)
        var zy2 = (zy * zy)
        if ((zx2 + zy2) > 4.0):
          discard `break`
        zy = (((2.0 * zx) * zy) + cy)
        zx = ((zx2 - zy2) + cx)
        i += 1
      frame[(row_base + x)] = int((float((255.0 * i)) / float(v_hoisted_cast_1)))
  return bytes(frame)

proc run_05_mandelbrot_zoom*(): auto =
  var width = 320
  var height = 240
  var frame_count = 48
  var max_iter = 110
  var center_x = (-0.743643887037151)
  var center_y = 0.13182590420533
  var base_scale = (float(3.2) / float(width))
  var zoom_per_frame = 0.93
  var out_path = "sample/out/05_mandelbrot_zoom.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  var scale = base_scale
  for v in 0 ..< frame_count:
    frames.add(render_frame(width, height, center_x, center_y, scale, max_iter))
    scale *= zoom_per_frame
  discard save_gif(out_path, width, height, frames, grayscale_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frame_count
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_05_mandelbrot_zoom()
