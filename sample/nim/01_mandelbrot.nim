include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc escape_count*(cx: float, cy: float, max_iter: int): auto =
  var x: float = 0.0
  var y: float = 0.0
  for i in 0 ..< max_iter:
    var x2: float = (x * x)
    var y2: float = (y * y)
    if ((x2 + y2) > 4.0):
      return i
    y = (((2.0 * x) * y) + cy)
    x = ((x2 - y2) + cx)
  return max_iter

proc color_map*(iter_count: int, max_iter: int): auto =
  if (iter_count >= max_iter):
    return (0, 0, 0)
  var t: float = (float(iter_count) / float(max_iter))
  var r: int = int((255.0 * (t * t)))
  var g: int = int((255.0 * t))
  var b: int = int((255.0 * (1.0 - t)))
  return (r, g, b)

proc render_mandelbrot*(width: int, height: int, max_iter: int, x_min: float, x_max: float, y_min: float, y_max: float): auto =
  var pixels: seq[uint8] = newSeq[uint8]()
  var v_hoisted_cast_1: float = float((height - 1))
  var v_hoisted_cast_2: float = float((width - 1))
  var v_hoisted_cast_3: float = float(max_iter)
  for y in 0 ..< height:
    var py: float = (y_min + ((y_max - y_min) * (float(y) / float(v_hoisted_cast_1))))
    for x in 0 ..< width:
      var px: float = (x_min + ((x_max - x_min) * (float(x) / float(v_hoisted_cast_2))))
      var it: int = escape_count(px, py, max_iter)
      var r: int
      var g: int
      var b: int
      if (it >= max_iter):
        r = 0
        g = 0
        b = 0
      else:
        var t: float = (float(it) / float(v_hoisted_cast_3))
        r = int((255.0 * (t * t)))
        g = int((255.0 * t))
        b = int((255.0 * (1.0 - t)))
      pixels.add(uint8(r))
      pixels.add(uint8(g))
      pixels.add(uint8(b))
  return pixels

proc run_mandelbrot*(): auto =
  var width: int = 1600
  var height: int = 1200
  var max_iter: int = 1000
  var out_path: string = "sample/out/01_mandelbrot.png"
  var start: float = epochTime()
  var pixels: seq[uint8] = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2)
  write_rgb_png(out_path, width, height, pixels)
  var elapsed: float = (epochTime() - start)
  echo "output:", out_path
  echo "size:", width, "x", height
  echo "max_iter:", max_iter
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_mandelbrot()
