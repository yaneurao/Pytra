require_relative "py_runtime"


# 11: Sample that outputs Lissajous-motion particles as a GIF.

def color_palette()
  p = __pytra_bytearray()
  i = 0
  while i < 256
    r = i
    g = (i * 3 % 256)
    b = 255 - i
    p.concat([r, g, b])
    i += 1
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
  t = 0
  while t < frames_n
    frame = __pytra_bytearray(w * h)
    __hoisted_cast_1 = __pytra_float(t)
    p = 0
    while p < particles
      phase = p * 0.261799
      x = __pytra_int((w * 0.5 + (w * 0.38 * Math.sin((0.11 * __hoisted_cast_1 + phase * 2.0)))))
      y = __pytra_int((h * 0.5 + (h * 0.38 * Math.sin((0.17 * __hoisted_cast_1 + phase * 3.0)))))
      color = (30 + (p * 9 % 220))
      dy = (-2)
      while dy < 3
        dx = (-2)
        while dx < 3
          xx = x + dx
          yy = y + dy
          if (xx >= 0) && (xx < w) && (yy >= 0) && (yy < h)
            d2 = (dx * dx + dy * dy)
            if d2 <= 4
              idx = (yy * w + xx)
              v = (color - d2 * 20)
              v = __pytra_max(0, v)
              if v > __pytra_get_index(frame, idx)
                __pytra_set_index(frame, idx, v)
              end
            end
          end
          dx += 1
        end
        dy += 1
      end
      p += 1
    end
    frames.append(__pytra_bytes(frame))
    t += 1
  end
  save_gif(out_path, w, h, frames, color_palette(), 3, 0)
  elapsed = __pytra_perf_counter() - start
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_11_lissajous_particles()
end
