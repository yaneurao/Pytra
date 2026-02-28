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

def julia_palette()
  palette = __pytra_bytearray((256 * 3))
  __pytra_set_index(palette, 0, 0)
  __pytra_set_index(palette, 1, 0)
  __pytra_set_index(palette, 2, 0)
  __step_0 = __pytra_int(1)
  i = __pytra_int(1)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    t = __pytra_div((i - 1), 254.0)
    r = __pytra_int((255.0 * ((((9.0 * (1.0 - t)) * t) * t) * t)))
    g = __pytra_int((255.0 * ((((15.0 * (1.0 - t)) * (1.0 - t)) * t) * t)))
    b = __pytra_int((255.0 * ((((8.5 * (1.0 - t)) * (1.0 - t)) * (1.0 - t)) * t)))
    __pytra_set_index(palette, ((i * 3) + 0), r)
    __pytra_set_index(palette, ((i * 3) + 1), g)
    __pytra_set_index(palette, ((i * 3) + 2), b)
    i += __step_0
  end
  return __pytra_bytes(palette)
end

def render_frame(width, height, cr, ci, max_iter, phase)
  frame = __pytra_bytearray((width * height))
  __hoisted_cast_1 = __pytra_float((height - 1))
  __hoisted_cast_2 = __pytra_float((width - 1))
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    row_base = (y * width)
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
        zy = (((2.0 * zx) * zy) + ci)
        zx = ((zx2 - zy2) + cr)
        i += 1
      end
      if __pytra_truthy((i >= max_iter))
        __pytra_set_index(frame, (row_base + x), 0)
      else
        color_index = (1 + (((__pytra_int((i * 224)) / __pytra_int(max_iter)) + phase) % 255))
        __pytra_set_index(frame, (row_base + x), color_index)
      end
      x += __step_1
    end
    y += __step_0
  end
  return __pytra_bytes(frame)
end

def run_06_julia_parameter_sweep()
  width = 320
  height = 240
  frames_n = 72
  max_iter = 180
  out_path = "sample/out/06_julia_parameter_sweep.gif"
  start = __pytra_perf_counter()
  frames = []
  center_cr = (-0.745)
  center_ci = 0.186
  radius_cr = 0.12
  radius_ci = 0.1
  start_offset = 20
  phase_offset = 180
  __hoisted_cast_3 = __pytra_float(frames_n)
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(frames_n)) || (__step_0 < 0 && i > __pytra_int(frames_n)))
    t = __pytra_div(((i + start_offset) % frames_n), __hoisted_cast_3)
    angle = ((2.0 * Math::PI) * t)
    cr = (center_cr + (radius_cr * Math.cos(__pytra_float(angle))))
    ci = (center_ci + (radius_ci * Math.sin(__pytra_float(angle))))
    phase = ((phase_offset + (i * 5)) % 255)
    frames.append(render_frame(width, height, cr, ci, max_iter, phase))
    i += __step_0
  end
  __pytra_noop(out_path, width, height, frames, julia_palette())
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_06_julia_parameter_sweep()
end
