# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 08: Sample that outputs Langton's Ant trajectories as a GIF.

def capture(grid, w, h)
  frame = __pytra_bytearray((w * h))
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)))
    row_base = (y * w)
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)))
      __pytra_set_index(frame, (row_base + x), (__pytra_truthy(__pytra_get_index(__pytra_get_index(grid, y), x)) ? 255 : 0))
      x += __step_1
    end
    y += __step_0
  end
  return __pytra_bytes(frame)
end

def run_08_langtons_ant()
  w = 420
  h = 420
  out_path = "sample/out/08_langtons_ant.gif"
  start = __pytra_perf_counter()
  grid = __pytra_list_comp_range(0, h, 1) { |__lc_i| ([0] * w) }
  x = (__pytra_int(w) / __pytra_int(2))
  y = (__pytra_int(h) / __pytra_int(2))
  d = 0
  steps_total = 600000
  capture_every = 3000
  frames = []
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(steps_total)) || (__step_0 < 0 && i > __pytra_int(steps_total)))
    if __pytra_truthy((__pytra_get_index(__pytra_get_index(grid, y), x) == 0))
      d = ((d + 1) % 4)
      __pytra_set_index(__pytra_get_index(grid, y), x, 1)
    else
      d = ((d + 3) % 4)
      __pytra_set_index(__pytra_get_index(grid, y), x, 0)
    end
    if __pytra_truthy((d == 0))
      y = (((y - 1) + h) % h)
    else
      if __pytra_truthy((d == 1))
        x = ((x + 1) % w)
      else
        if __pytra_truthy((d == 2))
          y = ((y + 1) % h)
        else
          x = (((x - 1) + w) % w)
        end
      end
    end
    if __pytra_truthy(((i % capture_every) == 0))
      frames.append(capture(grid, w, h))
    end
    i += __step_0
  end
  __pytra_noop(out_path, w, h, frames, [])
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", __pytra_len(frames))
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_08_langtons_ant()
end
