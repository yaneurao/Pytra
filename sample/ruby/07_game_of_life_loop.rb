# Auto-generated Pytra Ruby native source from EAST3.

def __pytra_noop(*args)
  nil
end

def __pytra_assert(*args)
  "True"
end

def __pytra_perf_counter
  Process.clock_gettime(Process::CLOCK_MONOTONIC)
end

def __pytra_truthy(v)
  return false if v.nil?
  return v if v == true || v == false
  return v != 0 if v.is_a?(Integer)
  return v != 0.0 if v.is_a?(Float)
  return !v.empty? if v.respond_to?(:empty?)
  true
end

def __pytra_int(v)
  return 0 if v.nil?
  return v.to_i
end

def __pytra_float(v)
  return 0.0 if v.nil?
  return v.to_f
end

def __pytra_div(a, b)
  lhs = __pytra_float(a)
  rhs = __pytra_float(b)
  raise ZeroDivisionError, 'division by zero' if rhs == 0.0
  lhs / rhs
end

def __pytra_str(v)
  return "" if v.nil?
  v.to_s
end

def __pytra_len(v)
  return 0 if v.nil?
  return v.length if v.respond_to?(:length)
  0
end

def __pytra_as_list(v)
  return v if v.is_a?(Array)
  return v.to_a if v.respond_to?(:to_a)
  []
end

def __pytra_as_dict(v)
  return v if v.is_a?(Hash)
  {}
end

def __pytra_bytearray(v=nil)
  return [] if v.nil?
  if v.is_a?(Integer)
    n = v
    n = 0 if n < 0
    return Array.new(n, 0)
  end
  if v.is_a?(String)
    return v.bytes
  end
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_bytes(v)
  return [] if v.nil?
  return v.bytes if v.is_a?(String)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << (__pytra_int(src[i]) & 255)
    i += 1
  end
  out
end

def __pytra_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << i
    i += step
  end
  out
end

def __pytra_list_comp_range(start_v, stop_v, step_v)
  out = []
  step = __pytra_int(step_v)
  return out if step == 0
  i = __pytra_int(start_v)
  stop = __pytra_int(stop_v)
  while ((step >= 0 && i < stop) || (step < 0 && i > stop))
    out << yield(i)
    i += step
  end
  out
end

def __pytra_enumerate(v)
  src = __pytra_as_list(v)
  out = []
  i = 0
  while i < src.length
    out << [i, src[i]]
    i += 1
  end
  out
end

def __pytra_abs(v)
  x = __pytra_float(v)
  x < 0 ? -x : x
end

def __pytra_get_index(container, index)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return nil if i < 0 || i >= container.length
    return container[i]
  end
  if container.is_a?(Hash)
    return container[index]
  end
  if container.is_a?(String)
    i = __pytra_int(index)
    i += container.length if i < 0
    return "" if i < 0 || i >= container.length
    return container[i] || ""
  end
  nil
end

def __pytra_set_index(container, index, value)
  if container.is_a?(Array)
    i = __pytra_int(index)
    i += container.length if i < 0
    return if i < 0 || i >= container.length
    container[i] = value
    return
  end
  if container.is_a?(Hash)
    container[index] = value
  end
end

def __pytra_slice(container, lower, upper)
  return nil if container.nil?
  lo = __pytra_int(lower)
  hi = __pytra_int(upper)
  return container[lo...hi]
end

def __pytra_min(a, b)
  __pytra_float(a) < __pytra_float(b) ? a : b
end

def __pytra_max(a, b)
  __pytra_float(a) > __pytra_float(b) ? a : b
end

def __pytra_isdigit(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[0-9]+\z/)
end

def __pytra_isalpha(v)
  s = __pytra_str(v)
  return false if s.empty?
  !!(s =~ /\A[A-Za-z]+\z/)
end

def __pytra_contains(container, item)
  return false if container.nil?
  return container.key?(item) if container.is_a?(Hash)
  return container.include?(item) if container.is_a?(Array)
  return container.include?(__pytra_str(item)) if container.is_a?(String)
  false
end

def __pytra_print(*args)
  if args.empty?
    puts
    return
  end
  puts(args.map { |x| __pytra_str(x) }.join(" "))
end

def next_state(grid, w, h)
  nxt = []
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)))
    row = []
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)))
      cnt = 0
      __step_2 = __pytra_int(1)
      dy = __pytra_int((-1))
      while ((__step_2 >= 0 && dy < __pytra_int(2)) || (__step_2 < 0 && dy > __pytra_int(2)))
        __step_3 = __pytra_int(1)
        dx = __pytra_int((-1))
        while ((__step_3 >= 0 && dx < __pytra_int(2)) || (__step_3 < 0 && dx > __pytra_int(2)))
          if __pytra_truthy((__pytra_truthy((dx != 0)) || __pytra_truthy((dy != 0))))
            nx = (((x + dx) + w) % w)
            ny = (((y + dy) + h) % h)
            cnt += __pytra_get_index(__pytra_get_index(grid, ny), nx)
          end
          dx += __step_3
        end
        dy += __step_2
      end
      alive = __pytra_get_index(__pytra_get_index(grid, y), x)
      if __pytra_truthy((__pytra_truthy((alive == 1)) && __pytra_truthy((__pytra_truthy((cnt == 2)) || __pytra_truthy((cnt == 3))))))
        row.append(1)
      else
        if __pytra_truthy((__pytra_truthy((alive == 0)) && __pytra_truthy((cnt == 3))))
          row.append(1)
        else
          row.append(0)
        end
      end
      x += __step_1
    end
    nxt.append(row)
    y += __step_0
  end
  return nxt
end

def render(grid, w, h, cell)
  width = (w * cell)
  height = (h * cell)
  frame = __pytra_bytearray((width * height))
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)))
      v = (__pytra_truthy(__pytra_get_index(__pytra_get_index(grid, y), x)) ? 255 : 0)
      __step_2 = __pytra_int(1)
      yy = __pytra_int(0)
      while ((__step_2 >= 0 && yy < __pytra_int(cell)) || (__step_2 < 0 && yy > __pytra_int(cell)))
        base = ((((y * cell) + yy) * width) + (x * cell))
        __step_3 = __pytra_int(1)
        xx = __pytra_int(0)
        while ((__step_3 >= 0 && xx < __pytra_int(cell)) || (__step_3 < 0 && xx > __pytra_int(cell)))
          __pytra_set_index(frame, (base + xx), v)
          xx += __step_3
        end
        yy += __step_2
      end
      x += __step_1
    end
    y += __step_0
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
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(h)) || (__step_0 < 0 && y > __pytra_int(h)))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(w)) || (__step_1 < 0 && x > __pytra_int(w)))
      noise = (((((x * 37) + (y * 73)) + ((x * y) % 19)) + ((x + y) % 11)) % 97)
      if __pytra_truthy((noise < 3))
        __pytra_set_index(__pytra_get_index(grid, y), x, 1)
      end
      x += __step_1
    end
    y += __step_0
  end
  glider = [[0, 1, 0], [0, 0, 1], [1, 1, 1]]
  r_pentomino = [[0, 1, 1], [1, 1, 0], [0, 1, 0]]
  lwss = [[0, 1, 1, 1, 1], [1, 0, 0, 0, 1], [0, 0, 0, 0, 1], [1, 0, 0, 1, 0]]
  __step_2 = __pytra_int(18)
  gy = __pytra_int(8)
  while ((__step_2 >= 0 && gy < __pytra_int((h - 8))) || (__step_2 < 0 && gy > __pytra_int((h - 8))))
    __step_3 = __pytra_int(22)
    gx = __pytra_int(8)
    while ((__step_3 >= 0 && gx < __pytra_int((w - 8))) || (__step_3 < 0 && gx > __pytra_int((w - 8))))
      kind = (((gx * 7) + (gy * 11)) % 3)
      if __pytra_truthy((kind == 0))
        ph = __pytra_len(glider)
        __step_4 = __pytra_int(1)
        py = __pytra_int(0)
        while ((__step_4 >= 0 && py < __pytra_int(ph)) || (__step_4 < 0 && py > __pytra_int(ph)))
          pw = __pytra_len(__pytra_get_index(glider, py))
          __step_5 = __pytra_int(1)
          px = __pytra_int(0)
          while ((__step_5 >= 0 && px < __pytra_int(pw)) || (__step_5 < 0 && px > __pytra_int(pw)))
            if __pytra_truthy((__pytra_get_index(__pytra_get_index(glider, py), px) == 1))
              __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
            end
            px += __step_5
          end
          py += __step_4
        end
      else
        if __pytra_truthy((kind == 1))
          ph = __pytra_len(r_pentomino)
          __step_6 = __pytra_int(1)
          py = __pytra_int(0)
          while ((__step_6 >= 0 && py < __pytra_int(ph)) || (__step_6 < 0 && py > __pytra_int(ph)))
            pw = __pytra_len(__pytra_get_index(r_pentomino, py))
            __step_7 = __pytra_int(1)
            px = __pytra_int(0)
            while ((__step_7 >= 0 && px < __pytra_int(pw)) || (__step_7 < 0 && px > __pytra_int(pw)))
              if __pytra_truthy((__pytra_get_index(__pytra_get_index(r_pentomino, py), px) == 1))
                __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
              end
              px += __step_7
            end
            py += __step_6
          end
        else
          ph = __pytra_len(lwss)
          __step_8 = __pytra_int(1)
          py = __pytra_int(0)
          while ((__step_8 >= 0 && py < __pytra_int(ph)) || (__step_8 < 0 && py > __pytra_int(ph)))
            pw = __pytra_len(__pytra_get_index(lwss, py))
            __step_9 = __pytra_int(1)
            px = __pytra_int(0)
            while ((__step_9 >= 0 && px < __pytra_int(pw)) || (__step_9 < 0 && px > __pytra_int(pw)))
              if __pytra_truthy((__pytra_get_index(__pytra_get_index(lwss, py), px) == 1))
                __pytra_set_index(__pytra_get_index(grid, ((gy + py) % h)), ((gx + px) % w), 1)
              end
              px += __step_9
            end
            py += __step_8
          end
        end
      end
      gx += __step_3
    end
    gy += __step_2
  end
  frames = []
  __step_11 = __pytra_int(1)
  __loop_10 = __pytra_int(0)
  while ((__step_11 >= 0 && __loop_10 < __pytra_int(steps)) || (__step_11 < 0 && __loop_10 > __pytra_int(steps)))
    frames.append(render(grid, w, h, cell))
    grid = next_state(grid, w, h)
    __loop_10 += __step_11
  end
  __pytra_noop(out_path, (w * cell), (h * cell), frames, [])
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", steps)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_07_game_of_life_loop()
end
