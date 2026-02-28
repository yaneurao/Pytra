require_relative "py_runtime"


# 11: Sample that outputs Lissajous-motion particles as a GIF.

def color_palette()
  p = __pytra_bytearray()
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    r = i
    g = ((i * 3) % 256)
    b = (255 - i)
    p.append(r)
    p.append(g)
    p.append(b)
    i += __step_0
  end
  return __pytra_bytes(p)
end

def run_11_lissajous_particles()
  w = 320
  h = 240
  frames_n = 360
  particles = 48
  out_path = "sample/out/11_lissajous_particles.gif"
  start = __pytra_perf_counter()
  frames = []
  __step_0 = __pytra_int(1)
  t = __pytra_int(0)
  while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)))
    frame = __pytra_bytearray((w * h))
    __hoisted_cast_1 = __pytra_float(t)
    __step_1 = __pytra_int(1)
    p = __pytra_int(0)
    while ((__step_1 >= 0 && p < __pytra_int(particles)) || (__step_1 < 0 && p > __pytra_int(particles)))
      phase = (p * 0.261799)
      x = __pytra_int(((w * 0.5) + ((w * 0.38) * Math.sin(__pytra_float(((0.11 * __hoisted_cast_1) + (phase * 2.0)))))))
      y = __pytra_int(((h * 0.5) + ((h * 0.38) * Math.sin(__pytra_float(((0.17 * __hoisted_cast_1) + (phase * 3.0)))))))
      color = (30 + ((p * 9) % 220))
      __step_2 = __pytra_int(1)
      dy = __pytra_int((-2))
      while ((__step_2 >= 0 && dy < __pytra_int(3)) || (__step_2 < 0 && dy > __pytra_int(3)))
        __step_3 = __pytra_int(1)
        dx = __pytra_int((-2))
        while ((__step_3 >= 0 && dx < __pytra_int(3)) || (__step_3 < 0 && dx > __pytra_int(3)))
          xx = (x + dx)
          yy = (y + dy)
          if __pytra_truthy((__pytra_truthy((xx >= 0)) && __pytra_truthy((xx < w)) && __pytra_truthy((yy >= 0)) && __pytra_truthy((yy < h))))
            d2 = ((dx * dx) + (dy * dy))
            if __pytra_truthy((d2 <= 4))
              idx = ((yy * w) + xx)
              v = (color - (d2 * 20))
              v = __pytra_max(0, v)
              if __pytra_truthy((v > __pytra_get_index(frame, idx)))
                __pytra_set_index(frame, idx, v)
              end
            end
          end
          dx += __step_3
        end
        dy += __step_2
      end
      p += __step_1
    end
    frames.append(__pytra_bytes(frame))
    t += __step_0
  end
  save_gif(out_path, w, h, frames, color_palette(), 3, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_11_lissajous_particles()
end
