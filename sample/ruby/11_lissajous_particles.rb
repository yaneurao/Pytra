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

def color_palette()
  p = __pytra_bytearray()
  __step_0 = __pytra_int(1)
  i = __pytra_int(0)
  while ((__step_0 >= 0 && i < __pytra_int(256)) || (__step_0 < 0 && i > __pytra_int(256)))
    r = i
    g = ((i * 3) % 256)
    b = (255 - i)
    p.append(r)
    p.append(g)
    p.append(b)
    i += __step_0
  end
  return __pytra_bytes(p)
end

def run_11_lissajous_particles()
  w = 320
  h = 240
  frames_n = 360
  particles = 48
  out_path = "sample/out/11_lissajous_particles.gif"
  start = __pytra_perf_counter()
  frames = []
  __step_0 = __pytra_int(1)
  t = __pytra_int(0)
  while ((__step_0 >= 0 && t < __pytra_int(frames_n)) || (__step_0 < 0 && t > __pytra_int(frames_n)))
    frame = __pytra_bytearray((w * h))
    __step_1 = __pytra_int(1)
    p = __pytra_int(0)
    while ((__step_1 >= 0 && p < __pytra_int(particles)) || (__step_1 < 0 && p > __pytra_int(particles)))
      phase = (p * 0.261799)
      x = __pytra_int(((w * 0.5) + ((w * 0.38) * Math.sin(__pytra_float(((0.11 * t) + (phase * 2.0)))))))
      y = __pytra_int(((h * 0.5) + ((h * 0.38) * Math.sin(__pytra_float(((0.17 * t) + (phase * 3.0)))))))
      color = (30 + ((p * 9) % 220))
      __step_2 = __pytra_int(1)
      dy = __pytra_int((-2))
      while ((__step_2 >= 0 && dy < __pytra_int(3)) || (__step_2 < 0 && dy > __pytra_int(3)))
        __step_3 = __pytra_int(1)
        dx = __pytra_int((-2))
        while ((__step_3 >= 0 && dx < __pytra_int(3)) || (__step_3 < 0 && dx > __pytra_int(3)))
          xx = (x + dx)
          yy = (y + dy)
          if __pytra_truthy((__pytra_truthy((xx >= 0)) && __pytra_truthy((xx < w)) && __pytra_truthy((yy >= 0)) && __pytra_truthy((yy < h))))
            d2 = ((dx * dx) + (dy * dy))
            if __pytra_truthy((d2 <= 4))
              idx = ((yy * w) + xx)
              v = (color - (d2 * 20))
              v = __pytra_max(0, v)
              if __pytra_truthy((v > __pytra_get_index(frame, idx)))
                __pytra_set_index(frame, idx, v)
              end
            end
          end
          dx += __step_3
        end
        dy += __step_2
      end
      p += __step_1
    end
    frames.append(__pytra_bytes(frame))
    t += __step_0
  end
  __pytra_noop(out_path, w, h, frames, color_palette())
  elapsed = (__pytra_perf_counter() - start)
  __pytra_print("output:", out_path)
  __pytra_print("frames:", frames_n)
  __pytra_print("elapsed_sec:", elapsed)
end

if __FILE__ == $PROGRAM_NAME
  run_11_lissajous_particles()
end
