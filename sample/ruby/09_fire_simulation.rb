require_relative "py_runtime"


# 09: Sample that outputs a simple fire effect as a GIF.

def fire_palette()
  p = __pytra_bytearray()
  i = 0
  while i < 256
    r = 0
    g = 0
    b = 0
    if (i < 85)
      r = (i * 3)
      g = 0
      b = 0
    else
      if (i < 170)
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
    i += 1
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
  t = 0
  while t < steps
    x = 0
    while x < w
      val = (170 + (((x * 13) + (t * 17)) % 86))
      __pytra_set_index(__pytra_get_index(heat, (h - 1)), x, val)
      x += 1
    end
    y = 1
    while y < h
      x = 0
      while x < w
        a = __pytra_get_index(__pytra_get_index(heat, y), x)
        b = __pytra_get_index(__pytra_get_index(heat, y), (((x - 1) + w) % w))
        c = __pytra_get_index(__pytra_get_index(heat, y), ((x + 1) % w))
        d = __pytra_get_index(__pytra_get_index(heat, ((y + 1) % h)), x)
        v = ((((a + b) + c) + d) / 4)
        cool = (1 + (((x + y) + t) % 3))
        nv = (v - cool)
        __pytra_set_index(__pytra_get_index(heat, (y - 1)), x, ((nv > 0) ? nv : 0))
        x += 1
      end
      y += 1
    end
    frame = __pytra_bytearray((w * h))
    yy = 0
    while yy < h
      row_base = (yy * w)
      xx = 0
      while xx < w
        __pytra_set_index(frame, (row_base + xx), __pytra_get_index(__pytra_get_index(heat, yy), xx))
        xx += 1
      end
      yy += 1
    end
    frames.append(__pytra_bytes(frame))
    t += 1
  end
  save_gif(out_path, w, h, frames, fire_palette(), 4, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", steps)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_09_fire_simulation()
end
