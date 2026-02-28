# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


def run_15_wave_interference_loop()
  w = 320
  h = 240
  frames_n = 96
  out_path = "sample/out/15_wave_interference_loop.gif"
  start = __pytra_perf_counter()
  frames = []
  __step_0 = __pytra_int(1)
  t = __pytra_int(0)
  while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)))
    frame = __pytra_bytearray((w * h))
    phase = (t * 0.12)
    __step_1 = __pytra_int(1)
    y = __pytra_int(0)
    while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)))
      row_base = (y * w)
      __step_2 = __pytra_int(1)
      x = __pytra_int(0)
      while ((__step_2 >= 0 && x < __pytra_int(w)) || (__step_2 < 0 && x > __pytra_int(w)))
        dx = (x - 160)
        dy = (y - 120)
        v = (((Math.sin(__pytra_float(((x + (t * 1.5)) * 0.045))) + Math.sin(__pytra_float(((y - (t * 1.2)) * 0.04)))) + Math.sin(__pytra_float((((x + y) * 0.02) + phase)))) + Math.sin(__pytra_float(((Math.sqrt(__pytra_float(((dx * dx) + (dy * dy)))) * 0.08) - (phase * 1.3)))))
        c = __pytra_int(((v + 4.0) * __pytra_div(255.0, 8.0)))
        if __pytra_truthy((c < 0))
          c = 0
        end
        if __pytra_truthy((c > 255))
          c = 255
        end
        __pytra_set_index(frame, (row_base + x), c)
        x += __step_2
      end
      y += __step_1
    end
    frames.append(__pytra_bytes(frame))
    t += __step_0
  end
  __pytra_noop(out_path, w, h, frames, [])
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_15_wave_interference_loop()
end
