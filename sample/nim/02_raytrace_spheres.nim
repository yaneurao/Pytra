include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc clamp01*(v: float): auto =
  if (v < 0.0):
    return 0.0
  if (v > 1.0):
    return 1.0
  return v

proc hit_sphere*(ox: float, oy: float, oz: float, dx: float, dy: float, dz: float, cx: float, cy: float, cz: float, r: float): auto =
  var lx: float = (ox - cx)
  var ly: float = (oy - cy)
  var lz: float = (oz - cz)
  var a: float = (((dx * dx) + (dy * dy)) + (dz * dz))
  var b: float = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
  var c: float = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
  var d: float = ((b * b) - ((4.0 * a) * c))
  if (d < 0.0):
    return (-1.0)
  var sd: float = /* unknown expr Unbox */
  var t0: float = (float(((-b) - sd)) / float((2.0 * a)))
  var t1: float = (float(((-b) + sd)) / float((2.0 * a)))
  if (t0 > 0.001):
    return t0
  if (t1 > 0.001):
    return t1
  return (-1.0)

proc render*(width: int, height: int, aa: int): auto =
  var pixels: seq[uint8] = newSeq[uint8]()
  var ox: float = 0.0
  var oy: float = 0.0
  var oz: float = (-3.0)
  var lx: float = (-0.4)
  var ly: float = 0.8
  var lz: float = (-0.45)
  var v_hoisted_cast_1: float = float(aa)
  var v_hoisted_cast_2: float = float((height - 1))
  var v_hoisted_cast_3: float = float((width - 1))
  var v_hoisted_cast_4: float = float(height)
  for y in 0 ..< height:
    for x in 0 ..< width:
      var ar: int = 0
      var ag: int = 0
      var ab: int = 0
      for ay in 0 ..< aa:
        for ax in 0 ..< aa:
          var fy = (float((y + (float((ay + 0.5)) / float(v_hoisted_cast_1)))) / float(v_hoisted_cast_2))
          var fx = (float((x + (float((ax + 0.5)) / float(v_hoisted_cast_1)))) / float(v_hoisted_cast_3))
          var sy: float = (1.0 - (2.0 * fy))
          var sx: float = (((2.0 * fx) - 1.0) * (float(width) / float(v_hoisted_cast_4)))
          var dx: float = sx
          var dy: float = sy
          var dz: float = 1.0
          var inv_len: float = /* unknown expr Unbox */
          dx *= inv_len
          dy *= inv_len
          dz *= inv_len
          var t_min: float = 1e+30
          var hit_id: int = (-1)
          var t: float = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8)
          if py_truthy(((t > 0.0) {op} (t < t_min))):
            t_min = t
            hit_id = 0
          t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
          if py_truthy(((t > 0.0) {op} (t < t_min))):
            t_min = t
            hit_id = 1
          t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0)
          if py_truthy(((t > 0.0) {op} (t < t_min))):
            t_min = t
            hit_id = 2
          var r: int = 0
          var g: int = 0
          var b: int = 0
          if (hit_id >= 0):
            var px: float = (ox + (dx * t_min))
            var py: float = (oy + (dy * t_min))
            var pz: float = (oz + (dz * t_min))
            var nx: float = 0.0
            var ny: float = 0.0
            var nz: float = 0.0
            if (hit_id == 0):
              nx = (float((px + 0.8)) / float(0.8))
              ny = (float((py + 0.2)) / float(0.8))
              nz = (float((pz - 2.2)) / float(0.8))
            elif (hit_id == 1):
              nx = (float((px - 0.9)) / float(0.95))
              ny = (float((py - 0.1)) / float(0.95))
              nz = (float((pz - 2.9)) / float(0.95))
            else:
              nx = 0.0
              ny = 1.0
              nz = 0.0
            var diff: float = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
            diff = clamp01(diff)
            var base_r: float = 0.0
            var base_g: float = 0.0
            var base_b: float = 0.0
            if (hit_id == 0):
              base_r = 0.95
              base_g = 0.35
              base_b = 0.25
            elif (hit_id == 1):
              base_r = 0.25
              base_g = 0.55
              base_b = 0.95
            else:
              var checker: int = (int(((px + 50.0) * 0.8)) + int(((pz + 50.0) * 0.8)))
              if (py_mod(checker, 2) == 0):
                base_r = 0.85
                base_g = 0.85
                base_b = 0.85
              else:
                base_r = 0.2
                base_g = 0.2
                base_b = 0.2
            var shade: float = (0.12 + (0.88 * diff))
            r = int((255.0 * clamp01((base_r * shade))))
            g = int((255.0 * clamp01((base_g * shade))))
            b = int((255.0 * clamp01((base_b * shade))))
          else:
            var tsky: float = (0.5 * (dy + 1.0))
            r = int((255.0 * (0.65 + (0.2 * tsky))))
            g = int((255.0 * (0.75 + (0.18 * tsky))))
            b = int((255.0 * (0.9 + (0.08 * tsky))))
          ar += r
          ag += g
          ab += b
      var samples = (aa * aa)
      pixels.add(uint8((ar div samples)))
      pixels.add(uint8((ag div samples)))
      pixels.add(uint8((ab div samples)))
  return pixels

proc run_raytrace*(): auto =
  var width: int = 1600
  var height: int = 900
  var aa: int = 2
  var out_path: string = "sample/out/02_raytrace_spheres.png"
  var start: float = epochTime()
  var pixels: seq[uint8] = render(width, height, aa)
  write_rgb_png(out_path, width, height, pixels)
  var elapsed: float = (epochTime() - start)
  echo "output:", out_path
  echo "size:", width, "x", height
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_raytrace()
