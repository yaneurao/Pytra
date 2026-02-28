# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 09: Sample that outputs a simple fire effect as a GIF.

def fire_palette()
  p = __pytra_bytearray()
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    r = 0
    g = 0
    b = 0
    if __pytra_truthy((i < 85))
      r = (i * 3)
      g = 0
      b = 0
    else
      if __pytra_truthy((i < 170))
        r = 255
        g = ((i - 85) * 3)
        b = 0
      else
        r = 255
        g = 255
        b = ((i - 170) * 3)
      end
    end
    p.append(r)
    p.append(g)
    p.append(b)
    i += __step_0
  end
  return __pytra_bytes(p)
end

def run_09_fire_simulation()
  w = 380
  h = 260
  steps = 420
  out_path = "sample/out/09_fire_simulation.gif"
  start = __pytra_perf_counter()
  heat = __pytra_list_comp_range(0, h, 1) { |__lc_i| ([0] * w) }
  frames = []
  __step_0 = __pytra_int(1)
  t = __pytra_int(0)
  while ((__step_0 >= 0 && t < __pytra_int(steps)) || (__step_0 < 0 && t > __pytra_int(steps)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)))
      val = (170 + (((x * 13) + (t * 17)) % 86))
      __pytra_set_index(__pytra_get_index(heat, (h - 1)), x, val)
      x += __step_1
    end
    __step_2 = __pytra_int(1)
    y = __pytra_int(1)
    while ((__step_2 >= 0 && y < __pytra_int(h)) || (__step_2 < 0 && y > __pytra_int(h)))
      __step_3 = __pytra_int(1)
      x = __pytra_int(0)
      while ((__step_3 >= 0 && x < __pytra_int(w)) || (__step_3 < 0 && x > __pytra_int(w)))
        a = __pytra_get_index(__pytra_get_index(heat, y), x)
        b = __pytra_get_index(__pytra_get_index(heat, y), (((x - 1) + w) % w))
        c = __pytra_get_index(__pytra_get_index(heat, y), ((x + 1) % w))
        d = __pytra_get_index(__pytra_get_index(heat, ((y + 1) % h)), x)
        v = (__pytra_int((((a + b) + c) + d)) / __pytra_int(4))
        cool = (1 + (((x + y) + t) % 3))
        nv = (v - cool)
        __pytra_set_index(__pytra_get_index(heat, (y - 1)), x, (__pytra_truthy((nv > 0)) ? nv : 0))
        x += __step_3
      end
      y += __step_2
    end
    frame = __pytra_bytearray((w * h))
    __step_4 = __pytra_int(1)
    yy = __pytra_int(0)
    while ((__step_4 >= 0 && yy < __pytra_int(h)) || (__step_4 < 0 && yy > __pytra_int(h)))
      row_base = (yy * w)
      __step_5 = __pytra_int(1)
      xx = __pytra_int(0)
      while ((__step_5 >= 0 && xx < __pytra_int(w)) || (__step_5 < 0 && xx > __pytra_int(w)))
        __pytra_set_index(frame, (row_base + xx), __pytra_get_index(__pytra_get_index(heat, yy), xx))
        xx += __step_5
      end
      yy += __step_4
    end
    frames.append(__pytra_bytes(frame))
    t += __step_0
  end
  __pytra_noop(out_path, w, h, frames, fire_palette())
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", steps)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_09_fire_simulation()
end
