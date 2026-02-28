# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


def clamp01(v)
  if __pytra_truthy((v < 0.0))
    return 0.0
  end
  if __pytra_truthy((v > 1.0))
    return 1.0
  end
  return v
end

def dot(ax, ay, az, bx, by, bz)
  return (((ax * bx) + (ay * by)) + (az * bz))
end

def length(x, y, z)
  return Math.sqrt(__pytra_float((((x * x) + (y * y)) + (z * z))))
end

def normalize(x, y, z)
  l = length(x, y, z)
  if __pytra_truthy((l < 1e-09))
    return [0.0, 0.0, 0.0]
  end
  return [__pytra_div(x, l), __pytra_div(y, l), __pytra_div(z, l)]
end

def reflect(ix, iy, iz, nx, ny, nz)
  d = (dot(ix, iy, iz, nx, ny, nz) * 2.0)
  return [(ix - (d * nx)), (iy - (d * ny)), (iz - (d * nz))]
end

def refract(ix, iy, iz, nx, ny, nz, eta)
  cosi = (-dot(ix, iy, iz, nx, ny, nz))
  sint2 = ((eta * eta) * (1.0 - (cosi * cosi)))
  if __pytra_truthy((sint2 > 1.0))
    return reflect(ix, iy, iz, nx, ny, nz)
  end
  cost = Math.sqrt(__pytra_float((1.0 - sint2)))
  k = ((eta * cosi) - cost)
  return [((eta * ix) + (k * nx)), ((eta * iy) + (k * ny)), ((eta * iz) + (k * nz))]
end

def schlick(cos_theta, f0)
  m = (1.0 - cos_theta)
  return (f0 + ((1.0 - f0) * ((((m * m) * m) * m) * m)))
end

def sky_color(dx, dy, dz, tphase)
  t = (0.5 * (dy + 1.0))
  r = (0.06 + (0.2 * t))
  g = (0.1 + (0.25 * t))
  b = (0.16 + (0.45 * t))
  band = (0.5 + (0.5 * Math.sin(__pytra_float((((8.0 * dx) + (6.0 * dz)) + tphase)))))
  r += (0.08 * band)
  g += (0.05 * band)
  b += (0.12 * band)
  return [clamp01(r), clamp01(g), clamp01(b)]
end

def sphere_intersect(ox, oy, oz, dx, dy, dz, cx, cy, cz, radius)
  lx = (ox - cx)
  ly = (oy - cy)
  lz = (oz - cz)
  b = (((lx * dx) + (ly * dy)) + (lz * dz))
  c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (radius * radius))
  h = ((b * b) - c)
  if __pytra_truthy((h < 0.0))
    return (-1.0)
  end
  s = Math.sqrt(__pytra_float(h))
  t0 = ((-b) - s)
  if __pytra_truthy((t0 > 0.0001))
    return t0
  end
  t1 = ((-b) + s)
  if __pytra_truthy((t1 > 0.0001))
    return t1
  end
  return (-1.0)
end

def palette_332()
  p = __pytra_bytearray((256 * 3))
  __hoisted_cast_1 = __pytra_float(7)
  __hoisted_cast_2 = __pytra_float(3)
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    r = ((i + 5) + 7)
    g = ((i + 2) + 7)
    b = (i + 3)
    __pytra_set_index(p, ((i * 3) + 0), __pytra_int(__pytra_div((255 * r), __hoisted_cast_1)))
    __pytra_set_index(p, ((i * 3) + 1), __pytra_int(__pytra_div((255 * g), __hoisted_cast_1)))
    __pytra_set_index(p, ((i * 3) + 2), __pytra_int(__pytra_div((255 * b), __hoisted_cast_2)))
    i += __step_0
  end
  return __pytra_bytes(p)
end

def quantize_332(r, g, b)
  rr = __pytra_int((clamp01(r) * 255.0))
  gg = __pytra_int((clamp01(g) * 255.0))
  bb = __pytra_int((clamp01(b) * 255.0))
  return ((((rr + 5) + 5) + ((gg + 5) + 2)) + (bb + 6))
end

def render_frame(width, height, frame_id, frames_n)
  t = __pytra_div(frame_id, frames_n)
  tphase = ((2.0 * Math::PI) * t)
  cam_r = 3.0
  cam_x = (cam_r * Math.cos(__pytra_float((tphase * 0.9))))
  cam_y = (1.1 + (0.25 * Math.sin(__pytra_float((tphase * 0.6)))))
  cam_z = (cam_r * Math.sin(__pytra_float((tphase * 0.9))))
  look_x = 0.0
  look_y = 0.35
  look_z = 0.0
  __tuple_0 = __pytra_as_list(normalize((look_x - cam_x), (look_y - cam_y), (look_z - cam_z)))
  fwd_x = __tuple_0[0]
  fwd_y = __tuple_0[1]
  fwd_z = __tuple_0[2]
  __tuple_1 = __pytra_as_list(normalize(fwd_z, 0.0, (-fwd_x)))
  right_x = __tuple_1[0]
  right_y = __tuple_1[1]
  right_z = __tuple_1[2]
  __tuple_2 = __pytra_as_list(normalize(((right_y * fwd_z) - (right_z * fwd_y)), ((right_z * fwd_x) - (right_x * fwd_z)), ((right_x * fwd_y) - (right_y * fwd_x))))
  up_x = __tuple_2[0]
  up_y = __tuple_2[1]
  up_z = __tuple_2[2]
  s0x = (0.9 * Math.cos(__pytra_float((1.3 * tphase))))
  s0y = (0.15 + (0.35 * Math.sin(__pytra_float((1.7 * tphase)))))
  s0z = (0.9 * Math.sin(__pytra_float((1.3 * tphase))))
  s1x = (1.2 * Math.cos(__pytra_float(((1.3 * tphase) + 2.094))))
  s1y = (0.1 + (0.4 * Math.sin(__pytra_float(((1.1 * tphase) + 0.8)))))
  s1z = (1.2 * Math.sin(__pytra_float(((1.3 * tphase) + 2.094))))
  s2x = (1.0 * Math.cos(__pytra_float(((1.3 * tphase) + 4.188))))
  s2y = (0.2 + (0.3 * Math.sin(__pytra_float(((1.5 * tphase) + 1.9)))))
  s2z = (1.0 * Math.sin(__pytra_float(((1.3 * tphase) + 4.188))))
  lr = 0.35
  lx = (2.4 * Math.cos(__pytra_float((tphase * 1.8))))
  ly = (1.8 + (0.8 * Math.sin(__pytra_float((tphase * 1.2)))))
  lz = (2.4 * Math.sin(__pytra_float((tphase * 1.8))))
  frame = __pytra_bytearray((width * height))
  aspect = __pytra_div(width, height)
  fov = 1.25
  __hoisted_cast_3 = __pytra_float(height)
  __hoisted_cast_4 = __pytra_float(width)
  __step_3 = __pytra_int(1)
  py = __pytra_int(0)
  while ((__step_3 >= 0 && py < __pytra_int(height)) || (__step_3 < 0 && py > __pytra_int(height)))
    row_base = (py * width)
    sy = (1.0 - __pytra_div((2.0 * (py + 0.5)), __hoisted_cast_3))
    __step_4 = __pytra_int(1)
    px = __pytra_int(0)
    while ((__step_4 >= 0 && px < __pytra_int(width)) || (__step_4 < 0 && px > __pytra_int(width)))
      sx = ((__pytra_div((2.0 * (px + 0.5)), __hoisted_cast_4) - 1.0) * aspect)
      rx = (fwd_x + (fov * ((sx * right_x) + (sy * up_x))))
      ry = (fwd_y + (fov * ((sx * right_y) + (sy * up_y))))
      rz = (fwd_z + (fov * ((sx * right_z) + (sy * up_z))))
      __tuple_5 = __pytra_as_list(normalize(rx, ry, rz))
      dx = __tuple_5[0]
      dy = __tuple_5[1]
      dz = __tuple_5[2]
      best_t = 1000000000.0
      hit_kind = 0
      r = 0.0
      g = 0.0
      b = 0.0
      if __pytra_truthy((dy < (-1e-06)))
        tf = __pytra_div(((-1.2) - cam_y), dy)
        if __pytra_truthy((__pytra_truthy((tf > 0.0001)) && __pytra_truthy((tf < best_t))))
          best_t = tf
          hit_kind = 1
        end
      end
      t0 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s0x, s0y, s0z, 0.65)
      if __pytra_truthy((__pytra_truthy((t0 > 0.0)) && __pytra_truthy((t0 < best_t))))
        best_t = t0
        hit_kind = 2
      end
      t1 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s1x, s1y, s1z, 0.72)
      if __pytra_truthy((__pytra_truthy((t1 > 0.0)) && __pytra_truthy((t1 < best_t))))
        best_t = t1
        hit_kind = 3
      end
      t2 = sphere_intersect(cam_x, cam_y, cam_z, dx, dy, dz, s2x, s2y, s2z, 0.58)
      if __pytra_truthy((__pytra_truthy((t2 > 0.0)) && __pytra_truthy((t2 < best_t))))
        best_t = t2
        hit_kind = 4
      end
      if __pytra_truthy((hit_kind == 0))
        __tuple_6 = __pytra_as_list(sky_color(dx, dy, dz, tphase))
        r = __tuple_6[0]
        g = __tuple_6[1]
        b = __tuple_6[2]
      else
        if __pytra_truthy((hit_kind == 1))
          hx = (cam_x + (best_t * dx))
          hz = (cam_z + (best_t * dz))
          cx = __pytra_int((__pytra_float((hx * 2.0))).floor)
          cz = __pytra_int((__pytra_float((hz * 2.0))).floor)
          checker = (__pytra_truthy((((cx + cz) % 2) == 0)) ? 0 : 1)
          base_r = (__pytra_truthy((checker == 0)) ? 0.1 : 0.04)
          base_g = (__pytra_truthy((checker == 0)) ? 0.11 : 0.05)
          base_b = (__pytra_truthy((checker == 0)) ? 0.13 : 0.08)
          lxv = (lx - hx)
          lyv = (ly - (-1.2))
          lzv = (lz - hz)
          __tuple_7 = __pytra_as_list(normalize(lxv, lyv, lzv))
          ldx = __tuple_7[0]
          ldy = __tuple_7[1]
          ldz = __tuple_7[2]
          ndotl = __pytra_max(ldy, 0.0)
          ldist2 = (((lxv * lxv) + (lyv * lyv)) + (lzv * lzv))
          glow = __pytra_div(8.0, (1.0 + ldist2))
          r = ((base_r + (0.8 * glow)) + (0.2 * ndotl))
          g = ((base_g + (0.5 * glow)) + (0.18 * ndotl))
          b = ((base_b + (1.0 * glow)) + (0.24 * ndotl))
        else
          cx = 0.0
          cy = 0.0
          cz = 0.0
          rad = 1.0
          if __pytra_truthy((hit_kind == 2))
            cx = s0x
            cy = s0y
            cz = s0z
            rad = 0.65
          else
            if __pytra_truthy((hit_kind == 3))
              cx = s1x
              cy = s1y
              cz = s1z
              rad = 0.72
            else
              cx = s2x
              cy = s2y
              cz = s2z
              rad = 0.58
            end
          end
          hx = (cam_x + (best_t * dx))
          hy = (cam_y + (best_t * dy))
          hz = (cam_z + (best_t * dz))
          __tuple_8 = __pytra_as_list(normalize(__pytra_div((hx - cx), rad), __pytra_div((hy - cy), rad), __pytra_div((hz - cz), rad)))
          nx = __tuple_8[0]
          ny = __tuple_8[1]
          nz = __tuple_8[2]
          __tuple_9 = __pytra_as_list(reflect(dx, dy, dz, nx, ny, nz))
          rdx = __tuple_9[0]
          rdy = __tuple_9[1]
          rdz = __tuple_9[2]
          __tuple_10 = __pytra_as_list(refract(dx, dy, dz, nx, ny, nz, __pytra_div(1.0, 1.45)))
          tdx = __tuple_10[0]
          tdy = __tuple_10[1]
          tdz = __tuple_10[2]
          __tuple_11 = __pytra_as_list(sky_color(rdx, rdy, rdz, tphase))
          sr = __tuple_11[0]
          sg = __tuple_11[1]
          sb = __tuple_11[2]
          __tuple_12 = __pytra_as_list(sky_color(tdx, tdy, tdz, (tphase + 0.8)))
          tr = __tuple_12[0]
          tg = __tuple_12[1]
          tb = __tuple_12[2]
          cosi = __pytra_max((-(((dx * nx) + (dy * ny)) + (dz * nz))), 0.0)
          fr = schlick(cosi, 0.04)
          r = ((tr * (1.0 - fr)) + (sr * fr))
          g = ((tg * (1.0 - fr)) + (sg * fr))
          b = ((tb * (1.0 - fr)) + (sb * fr))
          lxv = (lx - hx)
          lyv = (ly - hy)
          lzv = (lz - hz)
          __tuple_13 = __pytra_as_list(normalize(lxv, lyv, lzv))
          ldx = __tuple_13[0]
          ldy = __tuple_13[1]
          ldz = __tuple_13[2]
          ndotl = __pytra_max((((nx * ldx) + (ny * ldy)) + (nz * ldz)), 0.0)
          __tuple_14 = __pytra_as_list(normalize((ldx - dx), (ldy - dy), (ldz - dz)))
          hvx = __tuple_14[0]
          hvy = __tuple_14[1]
          hvz = __tuple_14[2]
          ndoth = __pytra_max((((nx * hvx) + (ny * hvy)) + (nz * hvz)), 0.0)
          spec = (ndoth * ndoth)
          spec = (spec * spec)
          spec = (spec * spec)
          spec = (spec * spec)
          glow = __pytra_div(10.0, (((1.0 + (lxv * lxv)) + (lyv * lyv)) + (lzv * lzv)))
          r += (((0.2 * ndotl) + (0.8 * spec)) + (0.45 * glow))
          g += (((0.18 * ndotl) + (0.6 * spec)) + (0.35 * glow))
          b += (((0.26 * ndotl) + (1.0 * spec)) + (0.65 * glow))
          if __pytra_truthy((hit_kind == 2))
            r *= 0.95
            g *= 1.05
            b *= 1.1
          else
            if __pytra_truthy((hit_kind == 3))
              r *= 1.08
              g *= 0.98
              b *= 1.04
            else
              r *= 1.02
              g *= 1.1
              b *= 0.95
            end
          end
        end
      end
      r = Math.sqrt(__pytra_float(clamp01(r)))
      g = Math.sqrt(__pytra_float(clamp01(g)))
      b = Math.sqrt(__pytra_float(clamp01(b)))
      __pytra_set_index(frame, (row_base + px), quantize_332(r, g, b))
      px += __step_4
    end
    py += __step_3
  end
  return __pytra_bytes(frame)
end

def run_16_glass_sculpture_chaos()
  width = 320
  height = 240
  frames_n = 72
  out_path = "sample/out/16_glass_sculpture_chaos.gif"
  start = __pytra_perf_counter()
  frames = []
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n)))
    frames.append(render_frame(width, height, i, frames_n))
    i += __step_0
  end
  __pytra_noop(out_path, width, height, frames, palette_332())
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_16_glass_sculpture_chaos()
end
