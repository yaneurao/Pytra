include "py_runtime.nim"

import std/os, std/times, std/tables, std/strutils, std/math

proc clamp01*(v: float): auto =
  if (v < 0.0):
    return 0.0
  if (v > 1.0):
    return 1.0
  return v

proc dot*(ax: float, ay: float, az: float, bx: float, by: float, bz: float): auto =
  return (((ax * bx) + (ay * by)) + (az * bz))

proc length*(x: float, y: float, z: float): auto =
  return sqrt((((x * x) + (y * y)) + (z * z)))

proc normalize*(x: float, y: float, z: float): auto =
  var l = length(x, y, z)
  if (l < 1e-09):
    return (0.0, 0.0, 0.0)
  return ((float(x) / float(l)), (float(y) / float(l)), (float(z) / float(l)))

proc reflect*(ix: float, iy: float, iz: float, nx: float, ny: float, nz: float): auto =
  var d = (dot(ix, iy, iz, nx, ny, nz) * 2.0)
  return ((ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz)))

proc refract*(ix: float, iy: float, iz: float, nx: float, ny: float, nz: float, eta: float): auto =
  var cosi = (-dot(ix, iy, iz, nx, ny, nz))
  var sint2 = ((eta * eta) * (1.0 - (cosi * cosi)))
  if (sint2 > 1.0):
    return reflect(ix, iy, iz, nx, ny, nz)
  var cost = sqrt((1.0 - sint2))
  var k = ((eta * cosi) - cost)
  return (((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz)))

proc schlick*(cos_theta: float, f0: float): auto =
  var m = (1.0 - cos_theta)
  return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))

proc sky_color*(dx: float, dy: float, dz: float, tphase: float): auto =
  var t = (0.5 * (dy + 1.0))
  var r = (0.06 + (0.2 * t))
  var g = (0.1 + (0.25 * t))
  var b = (0.16 + (0.45 * t))
  var band = (0.5 + (0.5 * math.sin((((8.0 * dx) + (6.0 * dz)) + tphase))))
  r += /* unknown expr Unbox */
  g += /* unknown expr Unbox */
  b += /* unknown expr Unbox */
  return (clamp01(r), clamp01(g), clamp01(b))

proc sphere_intersect*(ox: float, oy: float, oz: float, dx: float, dy: float, dz: float, cx: float, cy: float, cz: float, radius: float): auto =
  var lx = (ox - cx)
  var ly = (oy - cy)
  var lz = (oz - cz)
  var b = (((lx * dx) + (ly * dy)) + (lz * dz))
  var c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
  var h = ((b * b) - c)
  if (h < 0.0):
    return (-1.0)
  var s = sqrt(h)
  var t0 = ((-b) - s)
  if (t0 > 0.0001):
    return t0
  var t1 = ((-b) + s)
  if (t1 > 0.0001):
    return t1
  return (-1.0)

proc palette_332*(): auto =
  var p = newSeq[uint8]()
  var v_hoisted_cast_1: float = float(7)
  var v_hoisted_cast_2: float = float(3)
  for i in 0 ..< 256:
    var r = ((i + 5) + 7)
    var g = ((i + 2) + 7)
    var b = (i + 3)
    p[((i * 3) + 0)] = int((float((255 * r)) / float(v_hoisted_cast_1)))
    p[((i * 3) + 1)] = int((float((255 * g)) / float(v_hoisted_cast_1)))
    p[((i * 3) + 2)] = int((float((255 * b)) / float(v_hoisted_cast_2)))
  return bytes(p)

proc quantize_332*(r: float, g: float, b: float): auto =
  var rr = int((clamp01(r) * 255.0))
  var gg = int((clamp01(g) * 255.0))
  var bb = int((clamp01(b) * 255.0))
  return ((((rr + 5) + 5) + ((gg + 5) + 2)) + (bb + 6))

proc render_frame*(width: int, height: int, frame_id: int, frames_n: int): auto =
  var t = (float(frame_id) / float(frames_n))
  var tphase = ((2.0 * math.pi) * t)
  var cam_r = 3.0
  var cam_x = (cam_r * math.cos((tphase * 0.9)))
  var cam_y = (1.1 + (0.25 * math.sin((tphase * 0.6))))
  var cam_z = (cam_r * math.sin((tphase * 0.9)))
  var look_x = 0.0
  var look_y = 0.35
  var look_z = 0.0
  (fwd_x, fwd_y, fwd_z) = normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z))
  (right_x, right_y, right_z) = normalize(fwd_z, 0.0, (-fwd_x))
  (up_x, up_y, up_z) = normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x)))
  var s0x = (0.9 * math.cos((1.3 * tphase)))
  var s0y = (0.15 + (0.35 * math.sin((1.7 * tphase))))
  var s0z = (0.9 * math.sin((1.3 * tphase)))
  var s1x = (1.2 * math.cos(((1.3 * tphase) + 2.094)))
  var s1y = (0.1 + (0.4 * math.sin(((1.1 * tphase) + 0.8))))
  var s1z = (1.2 * math.sin(((1.3 * tphase) + 2.094)))
  var s2x = (1.0 * math.cos(((1.3 * tphase) + 4.188)))
  var s2y = (0.2 + (0.3 * math.sin(((1.5 * tphase) + 1.9))))
  var s2z = (1.0 * math.sin(((1.3 * tphase) + 4.188)))
  var lr = 0.35
  var lx = (2.4 * math.cos((tphase * 1.8)))
  var ly = (1.8 + (0.8 * math.sin((tphase * 1.2))))
  var lz = (2.4 * math.sin((tphase * 1.8)))
  var frame = newSeq[uint8]()
  var aspect = (float(width) / float(height))
  var fov = 1.25
  var v_hoisted_cast_3: float = float(height)
  var v_hoisted_cast_4: float = float(width)
  for py in 0 ..< height:
    var row_base = (py * width)
    var sy = (1.0 - (float((2.0 * (py + 0.5))) / float(v_hoisted_cast_3)))
    for px in 0 ..< width:
      var sx = (((float((2.0 * (px + 0.5))) / float(v_hoisted_cast_4)) - 1.0) * aspect)
      var rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))))
      var ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))))
      var rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))))
      (dx, dy, dz) = normalize(rx, ry, rz)
      var best_t = 1000000000.0
      var hit_kind = 0
      var r = 0.0
      var g = 0.0
      var b = 0.0
      if (dy < (-1e-06)):
        var tf = (float(((-1.2) - cam_y)) / float(dy))
        if py_truthy(((tf > 0.0001) {op} (tf < best_t))):
          best_t = /* unknown expr Unbox */
          hit_kind = 1
      var t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65)
      if py_truthy(((t0 > 0.0) {op} (t0 < best_t))):
        best_t = t0
        hit_kind = 2
      var t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72)
      if py_truthy(((t1 > 0.0) {op} (t1 < best_t))):
        best_t = t1
        hit_kind = 3
      var t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58)
      if py_truthy(((t2 > 0.0) {op} (t2 < best_t))):
        best_t = t2
        hit_kind = 4
      if (hit_kind == 0):
        (r, g, b) = sky_color(dx, dy, dz, tphase)
      elif (hit_kind == 1):
        var hx = (cam_x + (best_t * dx))
        var hz = (cam_z + (best_t * dz))
        var cx = int(math.floor((hx * 2.0)))
        var cz = int(math.floor((hz * 2.0)))
        var checker = /* unknown expr IfExp */
        var base_r = /* unknown expr IfExp */
        var base_g = /* unknown expr IfExp */
        var base_b = /* unknown expr IfExp */
        var lxv = (lx - hx)
        var lyv = (ly - (-1.2))
        var lzv = (lz - hz)
        (ldx, ldy, ldz) = normalize(lxv, lyv, lzv)
        var ndotl = max(ldy, 0.0)
        var ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv))
        var glow = (float(8.0) / float((1.0 + ldist2)))
        r = /* unknown expr Unbox */
        g = /* unknown expr Unbox */
        b = /* unknown expr Unbox */
      else:
        cx = 0.0
        var cy = 0.0
        cz = 0.0
        var rad = 1.0
        if (hit_kind == 2):
          cx = /* unknown expr Unbox */
          cy = /* unknown expr Unbox */
          cz = /* unknown expr Unbox */
          rad = 0.65
        elif (hit_kind == 3):
          cx = /* unknown expr Unbox */
          cy = /* unknown expr Unbox */
          cz = /* unknown expr Unbox */
          rad = 0.72
        else:
          cx = /* unknown expr Unbox */
          cy = /* unknown expr Unbox */
          cz = /* unknown expr Unbox */
          rad = 0.58
        hx = (cam_x + (best_t * dx))
        var hy = (cam_y + (best_t * dy))
        hz = (cam_z + (best_t * dz))
        (nx, ny, nz) = normalize((float((hx - cx)) / float(rad)), (float((hy - cy)) / float(rad)), (float((hz - cz)) / float(rad)))
        (rdx, rdy, rdz) = reflect(dx, dy, dz, nx, ny, nz)
        (tdx, tdy, tdz) = refract(dx, dy, dz, nx, ny, nz, (float(1.0) / float(1.45)))
        (sr, sg, sb) = sky_color(rdx, rdy, rdz, tphase)
        (tr, tg, tb) = sky_color(tdx, tdy, tdz, (tphase + 0.8))
        var cosi = max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0)
        var fr = schlick(cosi, 0.04)
        r = /* unknown expr Unbox */
        g = /* unknown expr Unbox */
        b = /* unknown expr Unbox */
        lxv = (lx - hx)
        lyv = (ly - hy)
        lzv = (lz - hz)
        (ldx, ldy, ldz) = normalize(lxv, lyv, lzv)
        ndotl = max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0)
        (hvx, hvy, hvz) = normalize((ldx - dx), (ldy - dy), (ldz - dz))
        var ndoth = max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0)
        var spec = (ndoth * ndoth)
        spec = (spec * spec)
        spec = (spec * spec)
        spec = (spec * spec)
        glow = (float(10.0) / float((((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv))))
        r += (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow))
        g += (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow))
        b += (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow))
        if (hit_kind == 2):
          r *= 0.95
          g *= 1.05
          b *= 1.1
        elif (hit_kind == 3):
          r *= 1.08
          g *= 0.98
          b *= 1.04
        else:
          r *= 1.02
          g *= 1.1
          b *= 0.95
      r = /* unknown expr Unbox */
      g = /* unknown expr Unbox */
      b = /* unknown expr Unbox */
      frame[(row_base + px)] = quantize_332(r, g, b)
  return bytes(frame)

proc run_16_glass_sculpture_chaos*(): auto =
  var width = 320
  var height = 240
  var frames_n = 72
  var out_path = "sample/out/16_glass_sculpture_chaos.gif"
  var start = epochTime()
  var frames: seq[auto] = @[]
  for i in 0 ..< frames_n:
    frames.add(render_frame(width, height, i, frames_n))
  discard save_gif(out_path, width, height, frames, palette_332())
  var elapsed = (epochTime() - start)
  echo "output:", out_path
  echo "frames:", frames_n
  echo "elapsed_sec:", elapsed


if isMainModule:
  run_16_glass_sculpture_chaos()
