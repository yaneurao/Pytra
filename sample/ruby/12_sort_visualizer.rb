require_relative "py_runtime"


# 12: Sample that outputs intermediate states of bubble sort as a GIF.

def render(values, w, h)
  frame = __pytra_bytearray((w * h))
  n = __pytra_len(values)
  bar_w = __pytra_div(w, n)
  __hoisted_cast_1 = __pytra_float(n)
  __hoisted_cast_2 = __pytra_float(h)
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n)))
    x0 = __pytra_int((i * bar_w))
    x1 = __pytra_int(((i + 1) * bar_w))
    if __pytra_truthy((x1 <= x0))
      x1 = (x0 + 1)
    end
    bh = __pytra_int((__pytra_div(__pytra_get_index(values, i), __hoisted_cast_1) * __hoisted_cast_2))
    y = (h - bh)
    __step_1 = __pytra_int(1)
    y = __pytra_int(y)
    while ((__step_1 >= 0 && y < __pytra_int(h)) || (__step_1 < 0 && y > __pytra_int(h)))
      __step_2 = __pytra_int(1)
      x = __pytra_int(x0)
      while ((__step_2 >= 0 && x < __pytra_int(x1)) || (__step_2 < 0 && x > __pytra_int(x1)))
        __pytra_set_index(frame, ((y * w) + x), 255)
        x += __step_2
      end
      y += __step_1
    end
    i += __step_0
  end
  return __pytra_bytes(frame)
end

def run_12_sort_visualizer()
  w = 320
  h = 180
  n = 124
  out_path = "sample/out/12_sort_visualizer.gif"
  start = __pytra_perf_counter()
  values = []
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(n)) || (__step_0 < 0 && i > __pytra_int(n)))
    values.append((((i * 37) + 19) % n))
    i += __step_0
  end
  frames = [render(values, w, h)]
  frame_stride = 16
  op = 0
  __step_1 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_1 >= 0 && i < __pytra_int(n)) || (__step_1 < 0 && i > __pytra_int(n)))
    swapped = false
    __step_2 = __pytra_int(1)
    j = __pytra_int(0)
    while ((__step_2 >= 0 && j < __pytra_int(((n - i) - 1))) || (__step_2 < 0 && j > __pytra_int(((n - i) - 1))))
      if __pytra_truthy((__pytra_get_index(values, j) > __pytra_get_index(values, (j + 1))))
        __tuple_3 = __pytra_as_list([__pytra_get_index(values, (j + 1)), __pytra_get_index(values, j)])
        __pytra_set_index(values, j, __tuple_3[0])
        __pytra_set_index(values, (j + 1), __tuple_3[1])
        swapped = true
      end
      if __pytra_truthy(((op % frame_stride) == 0))
        frames.append(render(values, w, h))
      end
      op += 1
      j += __step_2
    end
    if __pytra_truthy((!__pytra_truthy(swapped)))
      break
    end
    i += __step_1
  end
  save_gif(out_path, w, h, frames, grayscale_palette(), 3, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", __pytra_len(frames))
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_12_sort_visualizer()
end
