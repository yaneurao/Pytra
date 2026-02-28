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
  __pytra_noop(out_path, w, h, frames, [])
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", __pytra_len(frames))
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_12_sort_visualizer()
end
