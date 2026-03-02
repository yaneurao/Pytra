require_relative "py_runtime"


# 15: Sample that renders wave interference animation and writes a GIF.

def run_15_wave_interference_loop()
  w = 320
  h = 240
  frames_n = 96
  out_path = "sample/out/15_wave_interference_loop.gif"
  start = __pytra_perf_counter()
  frames = []
  t = 0
  while t < frames_n
    frame = __pytra_bytearray((w * h))
    phase = (t * 0.12)
    y = 0
    while y < h
      row_base = (y * w)
      x = 0
      while x < w
        dx = (x - 160)
        dy = (y - 120)
        v = (((Math.sin(((x + (t * 1.5)) * 0.045)) + Math.sin(((y - (t * 1.2)) * 0.04))) + Math.sin((((x + y) * 0.02) + phase))) + Math.sin(__pytra_float(((Math.sqrt(__pytra_float(((dx * dx) + (dy * dy)))) * 0.08) - (phase * 1.3)))))
        c = __pytra_int(((v + 4.0) * __pytra_div(255.0, 8.0)))
        if (c < 0)
          c = 0
        end
        if (c > 255)
          c = 255
        end
        __pytra_set_index(frame, (row_base + x), c)
        x += 1
      end
      y += 1
    end
    frames.append(__pytra_bytes(frame))
    t += 1
  end
  save_gif(out_path, w, h, frames, grayscale_palette(), 4, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_15_wave_interference_loop()
end
