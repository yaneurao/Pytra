require_relative "py_runtime"


# 07: Sample that outputs Game of Life evolution as a GIF.

def next_state(grid, w, h)
  nxt = []
  y = 0
  while y < h
    row = []
    x = 0
    while x < w
      cnt = 0
      dy = (-1)
      while dy < 2
        dx = (-1)
        while dx < 2
          if (dx != 0) || (dy != 0)
            nx = ((x + dx + w) % w)
            ny = ((y + dy + h) % h)
            cnt += __pytra_get_index(__pytra_get_index(grid, ny), nx)
          end
          dx += 1
        end
        dy += 1
      end
      alive = __pytra_get_index(__pytra_get_index(grid, y), x)
      if (alive == 1) && ((cnt == 2) || (cnt == 3))
        row.append(1)
      else
        if (alive == 0) && (cnt == 3)
          row.append(1)
        else
          row.append(0)
        end
      end
      x += 1
    end
    nxt.append(row)
    y += 1
  end
  return nxt
end

def render(grid, w, h, cell)
  width = w * cell
  height = h * cell
  frame = __pytra_bytearray(width * height)
  y = 0
  while y < h
    x = 0
    while x < w
      v = (__pytra_truthy(__pytra_get_index(__pytra_get_index(grid, y), x)) ? 255 : 0)
      yy = 0
      while yy < cell
        base = (((y * cell + yy) * width) + x * cell)
        xx = 0
        while xx < cell
          __pytra_set_index(frame, base + xx, v)
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

def run_07_game_of_life_loop()
  w = 144
  h = 108
  cell = 4
  steps = 105
  out_path = "sample/out/07_game_of_life_loop.gif"
  start = __pytra_perf_counter()
  grid = __pytra_list_comp_range(0, h, 1) { |__lc_i| ([0] * w) }
  y = 0
  while y < h
    x = 0
    while x < w
      noise = ((((x * 37 + y * 73) + (x * y % 19)) + ((x + y) % 11)) % 97)
      if noise < 3
        __pytra_set_index(__pytra_get_index(grid, y), x, 1)
      end
      x += 1
    end
    y += 1
  end
  glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
  r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]]
  lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]]
  gy = 8
  __step_0 = 18
  while ((__step_0 >= 0 && gy < h - 8) || (__step_0 < 0 && gy > h - 8))
    gx = 8
    __step_1 = 22
    while ((__step_1 >= 0 && gx < w - 8) || (__step_1 < 0 && gx > w - 8))
      kind = ((gx * 7 + gy * 11) % 3)
      if kind == 0
        ph = __pytra_len(glider)
        py = 0
        while py < ph
          pw = __pytra_len(__pytra_get_index(glider, py))
          px = 0
          while px < pw
            if __pytra_get_index(__pytra_get_index(glider, py), px) == 1
              __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
            end
            px += 1
          end
          py += 1
        end
      else
        if kind == 1
          ph = __pytra_len(r_pentomino)
          py = 0
          while py < ph
            pw = __pytra_len(__pytra_get_index(r_pentomino, py))
            px = 0
            while px < pw
              if __pytra_get_index(__pytra_get_index(r_pentomino, py), px) == 1
                __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
              end
              px += 1
            end
            py += 1
          end
        else
          ph = __pytra_len(lwss)
          py = 0
          while py < ph
            pw = __pytra_len(__pytra_get_index(lwss, py))
            px = 0
            while px < pw
              if __pytra_get_index(__pytra_get_index(lwss, py), px) == 1
                __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
              end
              px += 1
            end
            py += 1
          end
        end
      end
      gx += __step_1
    end
    gy += __step_0
  end
  frames = []
  __loop_2 = 0
  while __loop_2 < steps
    frames.append(render(grid, w, h, cell))
    grid = next_state(grid, w, h)
    __loop_2 += 1
  end
  save_gif(out_path, w * cell, h * cell, frames, grayscale_palette(), 4, 0)
  elapsed = __pytra_perf_counter() - start
  __pytra_print("output:", out_path)
  __pytra_print("frames:", steps)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_07_game_of_life_loop()
end
