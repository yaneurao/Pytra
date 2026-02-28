require_relative "py_runtime"


# 04: Sample that renders an orbit-trap Julia set and writes a PNG image.

def render_orbit_trap_julia(width, height, max_iter, cx, cy)
  pixels = __pytra_bytearray()
  __hoisted_cast_1 = __pytra_float((height - 1))
  __hoisted_cast_2 = __pytra_float((width - 1))
  __hoisted_cast_3 = __pytra_float(max_iter)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    zy0 = ((-1.3) + (2.6 * __pytra_div(y, __hoisted_cast_1)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      zx = ((-1.9) + (3.8 * __pytra_div(x, __hoisted_cast_2)))
      zy = zy0
      trap = 1000000000.0
      i = 0
      while __pytra_truthy((i < max_iter))
        ax = zx
        if __pytra_truthy((ax < 0.0))
          ax = (-ax)
        end
        ay = zy
        if __pytra_truthy((ay < 0.0))
          ay = (-ay)
        end
        dxy = (zx - zy)
        if __pytra_truthy((dxy < 0.0))
          dxy = (-dxy)
        end
        if __pytra_truthy((ax < trap))
          trap = ax
        end
        if __pytra_truthy((ay < trap))
          trap = ay
        end
        if __pytra_truthy((dxy < trap))
          trap = dxy
        end
        zx2 = (zx * zx)
        zy2 = (zy * zy)
        if __pytra_truthy(((zx2 + zy2) > 4.0))
          break
        end
        zy = (((2.0 * zx) * zy) + cy)
        zx = ((zx2 - zy2) + cx)
        i += 1
      end
      r = 0
      g = 0
      b = 0
      if __pytra_truthy((i >= max_iter))
        r = 0
        g = 0
        b = 0
      else
        trap_scaled = (trap * 3.2)
        if __pytra_truthy((trap_scaled > 1.0))
          trap_scaled = 1.0
        end
        if __pytra_truthy((trap_scaled < 0.0))
          trap_scaled = 0.0
        end
        t = __pytra_div(i, __hoisted_cast_3)
        tone = __pytra_int((255.0 * (1.0 - trap_scaled)))
        r = __pytra_int((tone * (0.35 + (0.65 * t))))
        g = __pytra_int((tone * (0.15 + (0.85 * (1.0 - t)))))
        b = __pytra_int((255.0 * (0.25 + (0.75 * t))))
        if __pytra_truthy((r > 255))
          r = 255
        end
        if __pytra_truthy((g > 255))
          g = 255
        end
        if __pytra_truthy((b > 255))
          b = 255
        end
      end
      pixels.append(r)
      pixels.append(g)
      pixels.append(b)
      x += __step_1
    end
    y += __step_0
  end
  return pixels
end

def run_04_orbit_trap_julia()
  width = 1920
  height = 1080
  max_iter = 1400
  out_path = "sample/out/04_orbit_trap_julia.png"
  start = __pytra_perf_counter()
  pixels = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889)
  write_rgb_png(out_path, width, height, pixels)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("size:", width, "x", height)
  __pytra_print("max_iter:", max_iter)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_04_orbit_trap_julia()
end
