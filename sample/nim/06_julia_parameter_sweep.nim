include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc julia_palette*(): auto =
  var palette = newSeq[uint8]()
  palette[0] = 0
  palette[1] = 0
  palette[2] = 0
  for i in 1 ..< 256:
    var t = (float((i - 1)) / float(254.0))
    var r = int((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)))
    var g = int((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)))
    var b = int((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)))
    palette[((i * 3) + 0)] = r
    palette[((i * 3) + 1)] = g
    palette[((i * 3) + 2)] = b
  return bytes(palette)

proc render_frame*(width: int, height: int, cr: float, ci: float, max_iter: int, phase: int): auto =
  var frame = newSeq[uint8]()
  var v_hoisted_cast_1: float = float((height - 1))
  var v_hoisted_cast_2: float = float((width - 1))
  for y in 0 ..< height:
    var row_base = (y * width)
    var zy0 = ((-1.2) + (2.4 * (float(y) / float(v_hoisted_cast_1))))
    for x in 0 ..< width:
      var zx = ((-1.8) + (3.6 * (float(x) / float(v_hoisted_cast_2))))
      var zy = zy0
      var i = 0
      while (i < max_iter):
        var zx2 = (zx * zx)
        var zy2 = (zy * zy)
        if ((zx2 + zy2) > 4.0):
          discard `break`
        zy = (((2.0 * zx) * zy) + ci)
        zx = ((zx2 - zy2) + cr)
        i += 1
      if (i >= max_iter):
        frame[(row_base + x)] = 0
      else:
        var color_index = (1 + py_mod((((i * 224) div max_iter) + phase), 255))
        frame[(row_base + x)] = color_index
  return bytes(frame)

proc run_06_julia_parameter_sweep*(): auto =
  var width = 320
  var height = 240
  var frames_n = 72
  var max_iter = 180
  var out_path = "sample/out/06_julia_parameter_sweep.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  var center_cr = (-0.745)
  var center_ci = 0.186
  var radius_cr = 0.12
  var radius_ci = 0.1
  var start_offset = 20
  var phase_offset = 180
  var v_hoisted_cast_3: float = float(frames_n)
  for i in 0 ..< frames_n:
    var t = (float(py_mod((i + start_offset), frames_n)) / float(v_hoisted_cast_3))
    var angle = ((2.0 * math.pi) * t)
    var cr = (center_cr + (radius_cr * math.cos(angle)))
    var ci = (center_ci + (radius_ci * math.sin(angle)))
    var phase = py_mod((phase_offset + (i * 5)), 255)
    frames.add(render_frame(width, height, cr, ci, max_iter, phase))
  discard save_gif(out_path, width, height, frames, julia_palette())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames_n
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_06_julia_parameter_sweep()
