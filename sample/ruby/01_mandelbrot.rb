require_relative "py_runtime"


# 01: Sample that outputs the Mandelbrot set as a PNG image.
# Syntax is kept straightforward with future transpilation in mind.

def escape_count(cx, cy, max_iter)
  x = 0.0
  y = 0.0
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(max_iter)) || (__step_0 < 0 && i > __pytra_int(max_iter)))
    x2 = (x * x)
    y2 = (y * y)
    if __pytra_truthy(((x2 + y2) > 4.0))
      return i
    end
    y = (((2.0 * x) * y) + cy)
    x = ((x2 - y2) + cx)
    i += __step_0
  end
  return max_iter
end

def color_map(iter_count, max_iter)
  if __pytra_truthy((iter_count >= max_iter))
    return [0, 0, 0]
  end
  t = __pytra_div(iter_count, max_iter)
  r = __pytra_int((255.0 * (t * t)))
  g = __pytra_int((255.0 * t))
  b = __pytra_int((255.0 * (1.0 - t)))
  return [r, g, b]
end

def render_mandelbrot(width, height, max_iter, x_min, x_max, y_min, y_max)
  pixels = __pytra_bytearray()
  __hoisted_cast_1 = __pytra_float((height - 1))
  __hoisted_cast_2 = __pytra_float((width - 1))
  __hoisted_cast_3 = __pytra_float(max_iter)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    py = (y_min + ((y_max - y_min) * __pytra_div(y, __hoisted_cast_1)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      px = (x_min + ((x_max - x_min) * __pytra_div(x, __hoisted_cast_2)))
      it = escape_count(px, py, max_iter)
      r = nil
      g = nil
      b = nil
      if __pytra_truthy((it >= max_iter))
        r = 0
        g = 0
        b = 0
      else
        t = __pytra_div(it, __hoisted_cast_3)
        r = __pytra_int((255.0 * (t * t)))
        g = __pytra_int((255.0 * t))
        b = __pytra_int((255.0 * (1.0 - t)))
      end
      pixels.append(r)
      pixels.append(g)
      pixels.append(b)
      x += __step_1
    end
    y += __step_0
  end
  return pixels
end

def run_mandelbrot()
  width = 1600
  height = 1200
  max_iter = 1000
  out_path = "sample/out/01_mandelbrot.png"
  start = __pytra_perf_counter()
  pixels = render_mandelbrot(width, height, max_iter, (-2.2), 1.0, (-1.2), 1.2)
  write_rgb_png(out_path, width, height, pixels)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("size:", width, "x", height)
  __pytra_print("max_iter:", max_iter)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_mandelbrot()
end
