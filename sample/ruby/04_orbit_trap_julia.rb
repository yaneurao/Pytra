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

def __pytra_print(*args)
  if args.empty?
    puts
    return
  end
  puts(args.map { |x| __pytra_str(x) }.join(" "))
end

def render_orbit_trap_julia(width, height, max_iter, cx, cy)
  pixels = __pytra_bytearray()
  __step_0 = __pytra_int(1)
  y = __pytra_int(0)
  while ((__step_0 >= 0 && y < __pytra_int(height)) || (__step_0 < 0 && y > __pytra_int(height)))
    zy0 = ((-1.3) + (2.6 * (y / (height - 1))))
    __step_1 = __pytra_int(1)
    x = __pytra_int(0)
    while ((__step_1 >= 0 && x < __pytra_int(width)) || (__step_1 < 0 && x > __pytra_int(width)))
      zx = ((-1.9) + (3.8 * (x / (width - 1))))
      zy = zy0
      trap = 1000000000.0
      i = 0
      while __pytra_truthy((i < max_iter))
        ax = zx
        if __pytra_truthy((ax < 0.0))
          ax = (-ax)
        end
        ay = zy
        if __pytra_truthy((ay < 0.0))
          ay = (-ay)
        end
        dxy = (zx - zy)
        if __pytra_truthy((dxy < 0.0))
          dxy = (-dxy)
        end
        if __pytra_truthy((ax < trap))
          trap = ax
        end
        if __pytra_truthy((ay < trap))
          trap = ay
        end
        if __pytra_truthy((dxy < trap))
          trap = dxy
        end
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
        trap_scaled = (trap * 3.2)
        if __pytra_truthy((trap_scaled > 1.0))
          trap_scaled = 1.0
        end
        if __pytra_truthy((trap_scaled < 0.0))
          trap_scaled = 0.0
        end
        t = (i / max_iter)
        tone = __pytra_int((255.0 * (1.0 - trap_scaled)))
        r = __pytra_int((tone * (0.35 + (0.65 * t))))
        g = __pytra_int((tone * (0.15 + (0.85 * (1.0 - t)))))
        b = __pytra_int((255.0 * (0.25 + (0.75 * t))))
        if __pytra_truthy((r > 255))
          r = 255
        end
        if __pytra_truthy((g > 255))
          g = 255
        end
        if __pytra_truthy((b > 255))
          b = 255
        end
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

def run_04_orbit_trap_julia()
  width = 1920
  height = 1080
  max_iter = 1400
  out_path = "sample/out/04_orbit_trap_julia.png"
  start = __pytra_perf_counter()
  pixels = render_orbit_trap_julia(width, height, max_iter, (-0.7269), 0.1889)
  __pytra_noop(out_path, width, height, pixels)
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("size:", width, "x", height)
  __pytra_print("max_iter:", max_iter)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_04_orbit_trap_julia()
end
