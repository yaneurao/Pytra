require_relative "py_runtime"


# 12: Sample that outputs intermediate states of bubble sort as a GIF.

def render(values, w, h)
  frame = __pytra_bytearray((w * h))
  n = __pytra_len(values)
  bar_w = __pytra_div(w, n)
  __hoisted_cast_1 = __pytra_float(n)
  __hoisted_cast_2 = __pytra_float(h)
  i = 0
  while i < n
    x0 = __pytra_int((i * bar_w))
    x1 = __pytra_int(((i + 1) * bar_w))
    if (x1 <= x0)
      x1 = (x0 + 1)
    end
    bh = __pytra_int((__pytra_div(__pytra_get_index(values, i), __hoisted_cast_1) * __hoisted_cast_2))
    y = (h - bh)
    y = y
    while y < h
      x = x0
      while x < x1
        __pytra_set_index(frame, ((y * w) + x), 255)
        x += 1
      end
      y += 1
    end
    i += 1
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
  i = 0
  while i < n
    values.append((((i * 37) + 19) % n))
    i += 1
  end
  frames = [render(values, w, h)]
  frame_stride = 16
  op = 0
  i = 0
  while i < n
    swapped = false
    j = 0
    while j < ((n - i) - 1)
      if (__pytra_get_index(values, j) > __pytra_get_index(values, (j + 1)))
        __tuple_0 = __pytra_as_list([__pytra_get_index(values, (j + 1)), __pytra_get_index(values, j)])
        __pytra_set_index(values, j, __tuple_0[0])
        __pytra_set_index(values, (j + 1), __tuple_0[1])
        swapped = true
      end
      if ((op % frame_stride) == 0)
        frames.append(render(values, w, h))
      end
      op += 1
      j += 1
    end
    if (!swapped)
      break
    end
    i += 1
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
