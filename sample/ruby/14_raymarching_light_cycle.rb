# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 14: Sample that outputs a moving-light scene in a simple raymarching style as a GIF.

def palette()
  p = __pytra_bytearray()
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    r = __pytra_min(255, __pytra_int((20 + (i * 0.9))))
    g = __pytra_min(255, __pytra_int((10 + (i * 0.7))))
    b = __pytra_min(255, (30 + i))
    p.append(r)
    p.append(g)
    p.append(b)
    i += __step_0
  end
  return __pytra_bytes(p)
end

def scene(x, y, light_x, light_y)
  x1 = (x + 0.45)
  y1 = (y + 0.2)
  x2 = (x - 0.35)
  y2 = (y - 0.15)
  r1 = Math.sqrt(__pytra_float(((x1 * x1) + (y1 * y1))))
  r2 = Math.sqrt(__pytra_float(((x2 * x2) + (y2 * y2))))
  blob = (Math.exp(__pytra_float((((-7.0) * r1) * r1))) + Math.exp(__pytra_float((((-8.0) * r2) * r2))))
  lx = (x - light_x)
  ly = (y - light_y)
  l = Math.sqrt(__pytra_float(((lx * lx) + (ly * ly))))
  lit = __pytra_div(1.0, (1.0 + ((3.5 * l) * l)))
  v = __pytra_int((((255.0 * blob) * lit) * 5.0))
  return __pytra_min(255, __pytra_max(0, v))
end

def run_14_raymarching_light_cycle()
  w = 320
  h = 240
  frames_n = 84
  out_path = "sample/out/14_raymarching_light_cycle.gif"
  start = __pytra_perf_counter()
  frames = []
  __hoisted_cast_1 = __pytra_float(frames_n)
  __hoisted_cast_2 = __pytra_float((h - 1))
  __hoisted_cast_3 = __pytra_float((w - 1))
  __step_0 = __pytra_int(1)
  t = __pytra_int(0)
  while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)))
    frame = __pytra_bytearray((w * h))
    a = ((__pytra_div(t, __hoisted_cast_1) * Math::PI) * 2.0)
    light_x = (0.75 * Math.cos(__pytra_float(a)))
    light_y = (0.55 * Math.sin(__pytra_float((a * 1.2))))
    __step_1 = __pytra_int(1)
    y = __pytra_int(0)
    while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)))
      row_base = (y * w)
      py = ((__pytra_div(y, __hoisted_cast_2) * 2.0) - 1.0)
      __step_2 = __pytra_int(1)
      x = __pytra_int(0)
      while ((__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w)))
        px = ((__pytra_div(x, __hoisted_cast_3) * 2.0) - 1.0)
        __pytra_set_index(frame, (row_base + x), scene(px, py, light_x, light_y))
        x += __step_2
      end
      y += __step_1
    end
    frames.append(__pytra_bytes(frame))
    t += __step_0
  end
  save_gif(out_path, w, h, frames, palette(), 3, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_14_raymarching_light_cycle()
end
