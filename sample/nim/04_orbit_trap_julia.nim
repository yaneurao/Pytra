include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc render_orbit_trap_julia*(width: int, height: int, max_iter: int, cx: float, cy: float): auto =
  var pixels: seq[uint8] = newSeq[uint8]()
  var v_hoisted_cast_1: float = float((height - 1))
  var v_hoisted_cast_2: float = float((width - 1))
  var v_hoisted_cast_3: float = float(max_iter)
  for y in 0 ..< height:
    var zy0: float = ((-1.3) + (2.6 * (float(y) / float(v_hoisted_cast_1))))
    for x in 0 ..< width:
      var zx: float = ((-1.9) + (3.8 * (float(x) / float(v_hoisted_cast_2))))
      var zy: float = zy0
      var trap: float = 1000000000.0
      var i: int = 0
      while (i < max_iter):
        var ax: float = zx
        if (ax < 0.0):
          ax = (-ax)
        var ay: float = zy
        if (ay < 0.0):
          ay = (-ay)
        var dxy: float = (zx - zy)
        if (dxy < 0.0):
          dxy = (-dxy)
        if (ax < trap):
          trap = ax
        if (ay < trap):
          trap = ay
        if (dxy < trap):
          trap = dxy
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
        var trap_scaled: float = (trap * 3.2)
        if (trap_scaled > 1.0):
          trap_scaled = 1.0
        if (trap_scaled < 0.0):
          trap_scaled = 0.0
        var t: float = (float(i) / float(v_hoisted_cast_3))
        var tone: int = int((255.0 * (1.0 - trap_scaled)))
        r = int((tone * (0.35 + (0.65 * t))))
        g = int((tone * (0.15 + (0.85 * (1.0 - t)))))
        b = int((255.0 * (0.25 + (0.75 * t))))
        if (r > 255):
          r = 255
        if (g > 255):
          g = 255
        if (b > 255):
          b = 255
      pixels.add(uint8(r))
      pixels.add(uint8(g))
      pixels.add(uint8(b))
  return pixels

proc run_04_orbit_trap_julia*(): auto =
  var width: int = 1920
  var height: int = 1080
  var max_iter: int = 1400
  var out_path: string = "sample/out/04_orbit_trap_julia.png"
  var start: float = epochTime()
  var pixels: seq[uint8] = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889)
  write_rgb_png(out_path, width, height, pixels)
  var elapsed: float = (epochTime() - start)
  echo "output:", out_path
  echo "size:", width, "x", height
  echo "max_iter:", max_iter
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_04_orbit_trap_julia()
