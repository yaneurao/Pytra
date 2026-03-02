include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc render_julia*(width: int, height: int, max_iter: int, cx: float, cy: float): auto =
  var pixels: seq[uint8] = newSeq[uint8]()
  var v_hoisted_cast_1: float = float((height - 1))
  var v_hoisted_cast_2: float = float((width - 1))
  var v_hoisted_cast_3: float = float(max_iter)
  for y in 0 ..< height:
    var zy0: float = ((-1.2) + (2.4 * (float(y) / float(v_hoisted_cast_1))))
    for x in 0 ..< width:
      var zx: float = ((-1.8) + (3.6 * (float(x) / float(v_hoisted_cast_2))))
      var zy: float = zy0
      var i: int = 0
      while (i < max_iter):
        var zx2: float = (zx * zx)
        var zy2: float = (zy * zy)
        if ((zx2 + zy2) > 4.0):
          discard `break`
        zy = (((2.0 * zx) * zy) + cy)
        zx = ((zx2 - zy2) + cx)
        i += 1
      var r: int = 0
      var g: int = 0
      var b: int = 0
      if (i >= max_iter):
        r = 0
        g = 0
        b = 0
      else:
        var t: float = (float(i) / float(v_hoisted_cast_3))
        r = int((255.0 * (0.2 + (0.8 * t))))
        g = int((255.0 * (0.1 + (0.9 * (t * t)))))
        b = int((255.0 * (1.0 - t)))
      pixels.add(uint8(r))
      pixels.add(uint8(g))
      pixels.add(uint8(b))
  return pixels

proc run_julia*(): auto =
  var width: int = 3840
  var height: int = 2160
  var max_iter: int = 20000
  var out_path: string = "sample/out/03_julia_set.png"
  var start: float = epochTime()
  var pixels: seq[uint8] = render_julia(width, height, max_iter, (-0.8), 0.156)
  write_rgb_png(out_path, width, height, pixels)
  var elapsed: float = (epochTime() - start)
  echo "output:", out_path
  echo "size:", width, "x", height
  echo "max_iter:", max_iter
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_julia()
