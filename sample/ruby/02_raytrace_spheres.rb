require_relative "py_runtime"


# 02: Sample that runs a mini sphere-only ray tracer and outputs a PNG image.
# Dependencies are kept minimal (time only) for transpilation compatibility.

def clamp01(v)
  if __pytra_truthy((v < 0.0))
    return 0.0
  end
  if __pytra_truthy((v > 1.0))
    return 1.0
  end
  return v
end

def hit_sphere(ox, oy, oz, dx, dy, dz, cx, cy, cz, r)
  lx = (ox - cx)
  ly = (oy - cy)
  lz = (oz - cz)
  a = (((dx * dx) + (dy * dy)) + (dz * dz))
  b = (2.0 * (((lx * dx) + (ly * dy)) + (lz * dz)))
  c = ((((lx * lx) + (ly * ly)) + (lz * lz)) - (r * r))
  d = ((b * b) - ((4.0 * a) * c))
  if __pytra_truthy((d < 0.0))
    return (-1.0)
  end
  sd = Math.sqrt(__pytra_float(d))
  t0 = __pytra_div(((-b) - sd), (2.0 * a))
  t1 = __pytra_div(((-b) + sd), (2.0 * a))
  if __pytra_truthy((t0 > 0.001))
    return t0
  end
  if __pytra_truthy((t1 > 0.001))
    return t1
  end
  return (-1.0)
end

def render(width, height, aa)
  pixels = __pytra_bytearray()
  ox = 0.0
  oy = 0.0
  oz = (-3.0)
  lx = (-0.4)
  ly = 0.8
  lz = (-0.45)
  __hoisted_cast_1 = __pytra_float(aa)
  __hoisted_cast_2 = __pytra_float((height - 1))
  __hoisted_cast_3 = __pytra_float((width - 1))
  __hoisted_cast_4 = __pytra_float(height)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      ar = 0
      ag = 0
      ab = 0
      __step_2 = __pytra_int(1)
      ay = __pytra_int(0)
      while ((__step_2 >= 0 && ay < __pytra_int(aa)) || (__step_2 < 0 && ay > __pytra_int(aa)))
        __step_3 = __pytra_int(1)
        ax = __pytra_int(0)
        while ((__step_3 >= 0 && ax < __pytra_int(aa)) || (__step_3 < 0 && ax > __pytra_int(aa)))
          fy = __pytra_div((y + __pytra_div((ay + 0.5), __hoisted_cast_1)), __hoisted_cast_2)
          fx = __pytra_div((x + __pytra_div((ax + 0.5), __hoisted_cast_1)), __hoisted_cast_3)
          sy = (1.0 - (2.0 * fy))
          sx = (((2.0 * fx) - 1.0) * __pytra_div(width, __hoisted_cast_4))
          dx = sx
          dy = sy
          dz = 1.0
          inv_len = __pytra_div(1.0, Math.sqrt(__pytra_float((((dx * dx) + (dy * dy)) + (dz * dz)))))
          dx *= inv_len
          dy *= inv_len
          dz *= inv_len
          t_min = 1e+30
          hit_id = (-1)
          t = hit_sphere(ox, oy, oz, dx, dy, dz, (-0.8), (-0.2), 2.2, 0.8)
          if __pytra_truthy((__pytra_truthy((t > 0.0)) && __pytra_truthy((t < t_min))))
            t_min = t
            hit_id = 0
          end
          t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.9, 0.1, 2.9, 0.95)
          if __pytra_truthy((__pytra_truthy((t > 0.0)) && __pytra_truthy((t < t_min))))
            t_min = t
            hit_id = 1
          end
          t = hit_sphere(ox, oy, oz, dx, dy, dz, 0.0, (-1001.0), 3.0, 1000.0)
          if __pytra_truthy((__pytra_truthy((t > 0.0)) && __pytra_truthy((t < t_min))))
            t_min = t
            hit_id = 2
          end
          r = 0
          g = 0
          b = 0
          if __pytra_truthy((hit_id >= 0))
            px = (ox + (dx * t_min))
            py = (oy + (dy * t_min))
            pz = (oz + (dz * t_min))
            nx = 0.0
            ny = 0.0
            nz = 0.0
            if __pytra_truthy((hit_id == 0))
              nx = __pytra_div((px + 0.8), 0.8)
              ny = __pytra_div((py + 0.2), 0.8)
              nz = __pytra_div((pz - 2.2), 0.8)
            else
              if __pytra_truthy((hit_id == 1))
                nx = __pytra_div((px - 0.9), 0.95)
                ny = __pytra_div((py - 0.1), 0.95)
                nz = __pytra_div((pz - 2.9), 0.95)
              else
                nx = 0.0
                ny = 1.0
                nz = 0.0
              end
            end
            diff = (((nx * (-lx)) + (ny * (-ly))) + (nz * (-lz)))
            diff = clamp01(diff)
            base_r = 0.0
            base_g = 0.0
            base_b = 0.0
            if __pytra_truthy((hit_id == 0))
              base_r = 0.95
              base_g = 0.35
              base_b = 0.25
            else
              if __pytra_truthy((hit_id == 1))
                base_r = 0.25
                base_g = 0.55
                base_b = 0.95
              else
                checker = (__pytra_int(((px + 50.0) * 0.8)) + __pytra_int(((pz + 50.0) * 0.8)))
                if __pytra_truthy(((checker % 2) == 0))
                  base_r = 0.85
                  base_g = 0.85
                  base_b = 0.85
                else
                  base_r = 0.2
                  base_g = 0.2
                  base_b = 0.2
                end
              end
            end
            shade = (0.12 + (0.88 * diff))
            r = __pytra_int((255.0 * clamp01((base_r * shade))))
            g = __pytra_int((255.0 * clamp01((base_g * shade))))
            b = __pytra_int((255.0 * clamp01((base_b * shade))))
          else
            tsky = (0.5 * (dy + 1.0))
            r = __pytra_int((255.0 * (0.65 + (0.2 * tsky))))
            g = __pytra_int((255.0 * (0.75 + (0.18 * tsky))))
            b = __pytra_int((255.0 * (0.9 + (0.08 * tsky))))
          end
          ar += r
          ag += g
          ab += b
          ax += __step_3
        end
        ay += __step_2
      end
      samples = (aa * aa)
      pixels.append((__pytra_int(ar) / __pytra_int(samples)))
      pixels.append((__pytra_int(ag) / __pytra_int(samples)))
      pixels.append((__pytra_int(ab) / __pytra_int(samples)))
      x += __step_1
    end
    y += __step_0
  end
  return pixels
end

def run_raytrace()
  width = 1600
  height = 900
  aa = 2
  out_path = "sample/out/02_raytrace_spheres.png"
  start = __pytra_perf_counter()
  pixels = render(width, height, aa)
  write_rgb_png(out_path, width, height, pixels)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("size:", width, "x", height)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_raytrace()
end
