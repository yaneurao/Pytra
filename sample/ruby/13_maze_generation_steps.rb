require_relative "py_runtime"


# 13: Sample that outputs DFS maze-generation progress as a GIF.

def capture(grid, w, h, scale)
  width = (w * scale)
  height = (h * scale)
  frame = __pytra_bytearray((width * height))
  y = 0
  while y < h
    x = 0
    while x < w
      v = ((__pytra_get_index(__pytra_get_index(grid, y), x) == 0) ? 255 : 40)
      yy = 0
      while yy < scale
        base = ((((y * scale) + yy) * width) + (x * scale))
        xx = 0
        while xx < scale
          __pytra_set_index(frame, (base + xx), v)
          xx += 1
        end
        yy += 1
      end
      x += 1
    end
    y += 1
  end
  return __pytra_bytes(frame)
end

def run_13_maze_generation_steps()
  cell_w = 89
  cell_h = 67
  scale = 5
  capture_every = 20
  out_path = "sample/out/13_maze_generation_steps.gif"
  start = __pytra_perf_counter()
  grid = __pytra_list_comp_range(0, cell_h, 1) { |__lc_i| ([1] * cell_w) }
  stack = [[1, 1]]
  __pytra_set_index(__pytra_get_index(grid, 1), 1, 0)
  dirs = [[2, 0], [(-2), 0], [0, 2], [0, (-2)]]
  frames = []
  step = 0
  while __pytra_truthy(stack)
    __tuple_0 = __pytra_as_list(__pytra_get_index(stack, (-1)))
    x = __tuple_0[0]
    y = __tuple_0[1]
    candidates = []
    k = 0
    while k < 4
      __tuple_1 = __pytra_as_list(__pytra_get_index(dirs, k))
      dx = __tuple_1[0]
      dy = __tuple_1[1]
      nx = (x + dx)
      ny = (y + dy)
      if ((nx >= 1) && (nx < (cell_w - 1)) && (ny >= 1) && (ny < (cell_h - 1)) && (__pytra_get_index(__pytra_get_index(grid, ny), nx) == 1))
        if (dx == 2)
          candidates.append([nx, ny, (x + 1), y])
        else
          if (dx == (-2))
            candidates.append([nx, ny, (x - 1), y])
          else
            if (dy == 2)
              candidates.append([nx, ny, x, (y + 1)])
            else
              candidates.append([nx, ny, x, (y - 1)])
            end
          end
        end
      end
      k += 1
    end
    if (__pytra_len(candidates) == 0)
      stack.pop()
    else
      sel = __pytra_get_index(candidates, ((((x * 17) + (y * 29)) + (__pytra_len(stack) * 13)) % __pytra_len(candidates)))
      __tuple_2 = __pytra_as_list(sel)
      nx = __tuple_2[0]
      ny = __tuple_2[1]
      wx = __tuple_2[2]
      wy = __tuple_2[3]
      __pytra_set_index(__pytra_get_index(grid, wy), wx, 0)
      __pytra_set_index(__pytra_get_index(grid, ny), nx, 0)
      stack.append([nx, ny])
    end
    if ((step % capture_every) == 0)
      frames.append(capture(grid, cell_w, cell_h, scale))
    end
    step += 1
  end
  frames.append(capture(grid, cell_w, cell_h, scale))
  save_gif(out_path, (cell_w * scale), (cell_h * scale), frames, grayscale_palette(), 4, 0)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", __pytra_len(frames))
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_13_maze_generation_steps()
end
