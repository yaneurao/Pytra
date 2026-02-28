# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 03: Sample that outputs a Julia set as a PNG image.
# Implemented with simple loop-centric logic for transpilation compatibility.

def render_julia(width, height, max_iter, cx, cy)
  pixels = __pytra_bytearray()
  __hoisted_cast_1 = __pytra_float((height - 1))
  __hoisted_cast_2 = __pytra_float((width - 1))
  __hoisted_cast_3 = __pytra_float(max_iter)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    zy0 = ((-1.2) + (2.4 * __pytra_div(y, __hoisted_cast_1)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      zx = ((-1.8) + (3.6 * __pytra_div(x, __hoisted_cast_2)))
      zy = zy0
      i = 0
      while __pytra_truthy((i < max_iter))
        zx2 = (zx * zx)
        zy2 = (zy * zy)
        if __pytra_truthy(((zx2 + zy2) > 4.0))
          break
        end
        zy = (((2.0 * zx) * zy) + cy)
        zx = ((zx2 - zy2) + cx)
        i += 1
      end
      r = 0
      g = 0
      b = 0
      if __pytra_truthy((i >= max_iter))
        r = 0
        g = 0
        b = 0
      else
        t = __pytra_div(i, __hoisted_cast_3)
        r = __pytra_int((255.0 * (0.2 + (0.8 * t))))
        g = __pytra_int((255.0 * (0.1 + (0.9 * (t * t)))))
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

def run_julia()
  width = 3840
  height = 2160
  max_iter = 20000
  out_path = "sample/out/03_julia_set.png"
  start = __pytra_perf_counter()
  pixels = render_julia(width, height, max_iter, (-0.8), 0.156)
  __pytra_noop(out_path, width, height, pixels)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("size:", width, "x", height)
  __pytra_print("max_iter:", max_iter)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_julia()
end
