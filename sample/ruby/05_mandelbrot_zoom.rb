# Auto-generated Pytra Ruby native source from EAST3.
# Runtime helpers are provided by py_runtime.rb in the same directory.
require_relative "py_runtime"


# 05: Sample that outputs a Mandelbrot zoom as an animated GIF.

def render_frame(width, height, center_x, center_y, scale, max_iter)
  frame = __pytra_bytearray((width * height))
  __hoisted_cast_1 = __pytra_float(max_iter)
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    row_base = (y * width)
    cy = (center_y + ((y - (height * 0.5)) * scale))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      cx = (center_x + ((x - (width * 0.5)) * scale))
      zx = 0.0
      zy = 0.0
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
      __pytra_set_index(frame, (row_base + x), __pytra_int(__pytra_div((255.0 * i), __hoisted_cast_1)))
      x += __step_1
    end
    y += __step_0
  end
  return __pytra_bytes(frame)
end

def run_05_mandelbrot_zoom()
  width = 320
  height = 240
  frame_count = 48
  max_iter = 110
  center_x = (-0.743643887037151)
  center_y = 0.13182590420533
  base_scale = __pytra_div(3.2, width)
  zoom_per_frame = 0.93
  out_path = "sample/out/05_mandelbrot_zoom.gif"
  start = __pytra_perf_counter()
  frames = []
  scale = base_scale
  __step_1 = __pytra_int(1)
  __loop_0 = __pytra_int(0)
  while ((__step_1 >= 0 && __loop_0 < __pytra_int(frame_count)) || (__step_1 < 0 && __loop_0 > __pytra_int(frame_count)))
    frames.append(render_frame(width, height, center_x, center_y, scale, max_iter))
    scale *= zoom_per_frame
    __loop_0 += __step_1
  end
  save_gif(out_path, width, height, frames, grayscale_palette(), 5, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frame_count)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_05_mandelbrot_zoom()
end
