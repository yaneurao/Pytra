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
